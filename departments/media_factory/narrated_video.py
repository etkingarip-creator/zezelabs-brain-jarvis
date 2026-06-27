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


def _wrap(text: str, width: int = 16) -> str:
    """Uzun satırı kısa parçalara böl (taşmayı önle — büyük fontta dar sar)."""
    words = text.split()
    lines, cur = [], ""
    for wd in words:
        if cur and len(cur) + len(wd) + 1 > width:
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
Style: Body,Arial,52,&H00FFFFFF,&H00000000,&H64000000,1,1,4,2,2,120,120,360
Style: Hook,Arial,64,&H0000F2FF,&H00000000,&H78000000,1,1,5,3,2,120,120,440
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
    """İngilizce neural seslendirme (edge-tts, ücretsiz). voice ile ses değişir
    (çocuk içeriği: en-US-AnaNeural neşeli/çocuk sesi)."""
    try:
        import edge_tts
        comm = edge_tts.Communicate(text, voice)
        await comm.save(mp3_path)
        return os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0
    except Exception:
        return False


def _make_music_bed(path: str, duration: float) -> bool:
    """Neşeli yumuşak müzik yatağı (ffmpeg sentez — C-major akor + tremolo). Şarkı hissi."""
    try:
        # C(261.63)+E(329.63)+G(392) majör akor, hafif tremolo, yumuşak
        expr = ("sine=frequency=261.63:duration=%.1f[c];sine=frequency=329.63:duration=%.1f[e];"
                "sine=frequency=392:duration=%.1f[g];[c][e][g]amix=inputs=3,"
                "tremolo=f=4:d=0.4,volume=0.5" % (duration, duration, duration))
        r = subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", expr, "-t", f"{duration:.2f}", path],
                           capture_output=True, text=True, timeout=60)
        return r.returncode == 0 and os.path.exists(path)
    except Exception:
        return False


async def build_narrated_video(segments: List[Dict], output_path: str, visuals_video: str,
                               aspect: str = "9:16", voice: str = "en-US-GuyNeural",
                               music: bool = False) -> Optional[str]:
    """Tam birleştirme: EN ses (+opsiyonel müzik) + görsel + TR altyazı → tek MP4."""
    workdir = tempfile.mkdtemp(prefix="narr_")
    audio = os.path.join(workdir, "voice.mp3")
    ass = os.path.join(workdir, "subs.ass")
    en_text = " ".join(s.get("en", "") for s in segments).strip()

    if not await synth_voice_en(en_text, audio, voice):
        return None
    dur = _ffprobe_duration(audio)
    if dur <= 0:
        return None
    build_ass(segments, dur, ass)
    if not (visuals_video and os.path.exists(visuals_video)):
        return None

    music_path = os.path.join(workdir, "music.wav")
    has_music = False
    if music:
        # Önce ACE-Step (gerçek müzik/şarkı, yerel ücretsiz); yoksa sentez yatak
        try:
            from departments.media_factory.music_engine import generate_music, is_available
            if is_available():
                mp = os.path.join(workdir, "ace.mp3")
                if generate_music(music if isinstance(music, str) else "upbeat background music, cinematic",
                                  mp, duration=int(dur) + 2):
                    music_path = mp
                    has_music = True
        except Exception:
            pass
        if not has_music:
            has_music = _make_music_bed(music_path, dur)

    ass_esc = ass.replace("\\", "/").replace(":", "\\:")
    # filter_complex: video (scale+crop+kenburns+altyazı) + ses (voice + opsiyonel müzik mix)
    vchain = (f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
              f"zoompan=z='min(zoom+0.0008,1.18)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30,"
              f"ass='{ass_esc}'[v]")
    cmd = ["ffmpeg", "-y", "-stream_loop", "-1", "-i", visuals_video, "-i", audio]
    if has_music:
        cmd += ["-i", music_path]
        fc = (vchain + ";[1:a]volume=1.0,aresample=44100[vo];[2:a]volume=0.16,aresample=44100[mu];"
              "[vo][mu]amix=inputs=2:duration=first:dropout_transition=0[a]")
    else:
        fc = vchain + ";[1:a]aresample=44100[a]"
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]",
            "-t", f"{dur:.2f}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", output_path]
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
