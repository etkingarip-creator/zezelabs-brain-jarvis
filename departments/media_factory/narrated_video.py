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


def build_srt(segments: List[Dict], total_duration: float, srt_path: str) -> None:
    """TR altyazı SRT'si — segmentleri EN uzunluğuna göre orantılı zamanla."""
    weights = [max(1, len(s.get("en", ""))) for s in segments]
    tot = sum(weights) or 1
    t = 0.0
    lines = []
    for i, (seg, wt) in enumerate(zip(segments, weights), 1):
        dur = total_duration * (wt / tot)
        start, end = t, min(total_duration, t + dur)
        lines.append(f"{i}\n{_srt_time(start)} --> {_srt_time(end)}\n{seg.get('tr','').strip()}\n")
        t = end
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


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
    srt = os.path.join(workdir, "subs.srt")
    en_text = " ".join(s.get("en", "") for s in segments).strip()

    if not await synth_voice_en(en_text, audio):
        return None
    dur = _ffprobe_duration(audio)
    if dur <= 0:
        return None
    build_srt(segments, dur, srt)

    if not (visuals_video and os.path.exists(visuals_video)):
        return None

    # ffmpeg: görseli ses süresine döngüle + TR altyazı yak + EN sesi bindir
    srt_esc = srt.replace("\\", "/").replace(":", "\\:")
    style = "FontSize=16,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Alignment=2,MarginV=60"
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", visuals_video,   # görseli döngüle
        "-i", audio,                                  # EN ses
        "-vf", f"subtitles='{srt_esc}':force_style='{style}'",
        "-map", "0:v:0", "-map", "1:a:0",
        "-t", f"{dur:.2f}", "-c:v", "libx264", "-c:a", "aac", "-shortest",
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
