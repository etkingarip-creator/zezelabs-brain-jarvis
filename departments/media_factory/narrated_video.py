"""
Narrated Video — tam yayına-hazır video: EN seslendirme + TR altyazı + görsel + ffmpeg.

Ücretsiz: edge-tts (İngilizce neural ses) + ffmpeg (altyazı yakma + ses birleştirme).
Görsel katmanı VideoPipeline'dan (ücretsiz Layer 3 veya GLM). Segment-bazlı: LLM her
segment için {en, tr} verir → EN seslendirilir, TR altyazıya yakılır.
"""
from __future__ import annotations
import os
import asyncio
import subprocess
import tempfile
from typing import List, Dict, Optional


def _ffprobe_duration(path: str) -> float:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=30)
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def _srt_time(sec: float) -> str:
    h = int(sec // 3600); m = int((sec % 3600) // 60); s = int(sec % 60); ms = int((sec - int(sec)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _ass_time(sec: float) -> str:
    h = int(sec // 3600); m = int((sec % 3600) // 60); s = sec % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def _wrap(text: str, width: int = 24) -> str:
    """Uzun satırı kısa parçalara böl (mobil okunabilirlik — tek satıra sığsın)."""
    words = text.split()
    lines, cur = [], ""
    for wd in words:
        if len(cur) + len(wd) + 1 > width:
            lines.append(cur); cur = wd
        else:
            cur = (cur + " " + wd).strip()
    if cur:
        lines.append(cur)
    return "\\N".join(lines[:2])  # max 2 satır


def build_ass(segments: List[Dict], total_duration: float, ass_path: str,
              play_w: int = 1080, play_h: int = 1920) -> None:
    """Viral-stil TR altyazı (ASS): büyük kalın font, güçlü outline+gölge, alt-üçte-bir konum.
    HİYERARŞİ: ilk segment (hook) daha büyük + sarı. Diğerleri beyaz."""
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {play_w}
PlayResY: {play_h}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV
Style: Body,Arial,72,&H00FFFFFF,&H00000000,&H64000000,1,1,5,3,2,80,80,420
Style: Hook,Arial,92,&H0000F2FF,&H00000000,&H78000000,1,1,6,4,2,60,60,520
"""
    weights = [max(1, len(s.get("en", ""))) for s in segments]
    tot = sum(weights) or 1
    t = 0.0
    events = ["[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for i, (seg, wt) in enumerate(zip(segments, weights)):
        dur = total_duration * (wt / tot)
        start, end = t, min(total_duration, t + dur)
        style = "Hook" if i == 0 else "Body"
        txt = _wrap(seg.get("tr", "").strip().upper() if i == 0 else seg.get("tr", "").strip())
        events.append(f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},{style},,0,0,0,,{txt}")
        t = end
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(header + "\n" + "\n".join(events) + "\n")


async def synth_voice_en(text: str, mp3_path: str, voice: str = "en-US-GuyNeural") -> bool:
    """İngilizce neural seslendirme (edge-tts, ücretsiz)."""
    try:
        import edge_tts
        comm = edge_tts.Communicate(text, voice)
        await comm.save(mp3_path)
        return os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0
    except Exception:
        return False


async def build_narrated_video(segments: List[Dict], output_path: str,
                               visuals_video: str, aspect: str = "9:16") -> Optional[str]:
    """Tam birleştirme: EN ses + görsel + TR altyazı → tek MP4.
    segments: [{en, tr}]. visuals_video: önceden üretilmiş (sessiz) görsel MP4."""
    workdir = tempfile.mkdtemp(prefix="narr_")
    audio = os.path.join(workdir, "voice.mp3")
    ass = os.path.join(workdir, "subs.ass")
    en_text = " ".join(s.get("en", "") for s in segments).strip()

    if not await synth_voice_en(en_text, audio):
        return None
    dur = _ffprobe_duration(audio)
    if dur <= 0:
        return None
    build_ass(segments, dur, ass)

    if not (visuals_video and os.path.exists(visuals_video)):
        return None

    # Ken Burns (yavaş zoom) hareket + stillendirilmiş ASS altyazı + EN ses bindirme
    ass_esc = ass.replace("\\", "/").replace(":", "\\:")
    vf = (f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
          f"zoompan=z='min(zoom+0.0008,1.18)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30,"
          f"ass='{ass_esc}'")
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", visuals_video,   # görseli döngüle
        "-i", audio,                                  # EN ses
        "-vf", vf,
        "-map", "0:v:0", "-map", "1:a:0",
        "-t", f"{dur:.2f}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest",
        output_path,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if r.returncode == 0 and os.path.exists(output_path):
            return output_path
        return None
    except Exception:
        return None
    finally:
        try:
            import shutil
            shutil.rmtree(workdir, ignore_errors=True)
        except Exception:
            pass
