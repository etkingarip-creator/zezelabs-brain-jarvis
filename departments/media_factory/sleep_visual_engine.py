"""
Sleep Sinematik Ambient Görsel Motoru — uzun (2-4 saat) uyku videoları için.

Tek sabit görsel YETERSİZ. Bu motor: çok sakin sahne + yumuşak crossfade +
koyu/sıcak sinematik renk grade + vignette + çok yavaş Ken Burns → düşük-uyarım
ama zengin/bütünleşik görsel. Pexels ambient video (key varsa) veya AI görsel (yedek).

Maliyet: $0 (Pexels ücretsiz / Pollinations key'siz) + yerel ffmpeg.
"""
from __future__ import annotations
import os
import math
import subprocess
from typing import List, Optional

from departments.media_factory.broll_engine import (fetch_pexels_clips, fetch_pixabay_clips,
                                                     fetch_pollinations_images)

# Uyku-dostu sahne temaları (düşük uyarım, sıcak/sakin)
SLEEP_THEMES = [
    "rain on window night", "cozy fireplace embers", "misty forest fog slow",
    "calm ocean waves night", "starry night sky timelapse slow", "candle flame dark",
    "snowfall night forest", "northern lights aurora slow", "quiet lake reflection dusk",
    "cabin window storm", "moonlit clouds drifting", "autumn forest soft light",
]


def _scene_from_clip(src: str, out: str, sec: float, W: int, H: int, vertical: bool) -> Optional[str]:
    """Bir klibi sinematik sleep sahnesine çevir: kapla+kırp, yavaş Ken Burns, koyu/sıcak grade, vignette."""
    grade = ("eq=brightness=-0.07:saturation=0.85:contrast=0.95,"
             "colorbalance=rm=0.06:gm=0.0:bm=-0.06:rs=0.03:bs=-0.04,"  # sıcak ton
             "vignette=PI/4")
    kb = f"zoompan=z='min(zoom+0.0004,1.12)':d={int(sec*30)}:s={W}x{H}:fps=30"
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,{kb},{grade}")
    subprocess.run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", src, "-t", str(sec),
                    "-an", "-vf", vf, "-r", "30", "-c:v", "libx264", "-preset", "veryfast",
                    "-pix_fmt", "yuv420p", out], capture_output=True, timeout=300)
    return out if os.path.exists(out) and os.path.getsize(out) > 5000 else None


def _scene_from_image(img: str, out: str, sec: float, W: int, H: int) -> Optional[str]:
    grade = ("eq=brightness=-0.07:saturation=0.85:contrast=0.95,"
             "colorbalance=rm=0.06:bm=-0.06,vignette=PI/4")
    kb = f"zoompan=z='min(zoom+0.0004,1.12)':d={int(sec*30)}:s={W}x{H}:fps=30"
    vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,{kb},{grade}"
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", img, "-t", str(sec),
                    "-vf", vf, "-r", "30", "-c:v", "libx264", "-preset", "veryfast",
                    "-pix_fmt", "yuv420p", out], capture_output=True, timeout=300)
    return out if os.path.exists(out) and os.path.getsize(out) > 5000 else None


def _xfade_concat(scenes: List[str], out: str, xfade: float, scene_sec: float) -> Optional[str]:
    """Sahneleri yumuşak crossfade ile zincirle (ardışık xfade, sağlam)."""
    if len(scenes) == 1:
        subprocess.run(["ffmpeg", "-y", "-i", scenes[0], "-c", "copy", out], capture_output=True, timeout=120)
        return out if os.path.exists(out) else None
    cur = scenes[0]
    work = os.path.dirname(out)
    offset = scene_sec - xfade
    for i in range(1, len(scenes)):
        nxt = os.path.join(work, f"_xf_{i}.mp4")
        fc = f"[0:v][1:v]xfade=transition=fade:duration={xfade}:offset={offset}[v]"
        r = subprocess.run(["ffmpeg", "-y", "-i", cur, "-i", scenes[i],
                            "-filter_complex", fc, "-map", "[v]",
                            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", nxt],
                           capture_output=True, timeout=600)
        if not (os.path.exists(nxt) and os.path.getsize(nxt) > 5000):
            return cur  # zincir kırılırsa eldekini döndür
        cur = nxt
        offset += (scene_sec - xfade)
    subprocess.run(["ffmpeg", "-y", "-i", cur, "-c", "copy", out], capture_output=True, timeout=120)
    return out if os.path.exists(out) else cur


def build_cinematic_ambient(duration_sec: float, out_path: str, theme_keywords: Optional[List[str]] = None,
                            vertical: bool = False, scenes: int = 12, scene_sec: float = 150.0,
                            xfade: float = 2.5, loop: bool = True) -> Optional[dict]:
    """Uzun uyku videosu için sinematik ambient görsel (sessiz).
    loop=True → duration_sec'e döngüler. loop=False → sadece crossfade base montaj döner
    (çağıran taraf —ör. sleep_story— kendi sürесine döngüleyecekse çift encode'u önler)."""
    work = os.path.dirname(out_path)
    os.makedirs(work, exist_ok=True)
    W, H = (1080, 1920) if vertical else (1920, 1080)
    themes = (theme_keywords or SLEEP_THEMES)[:scenes]

    # 1. Kaynak: Pexels video (tercih) → yoksa AI görsel
    src = "pexels"
    clips = fetch_pexels_clips(themes, os.path.join(work, "pex_amb"), count=scenes, vertical=vertical)
    if len(clips) < scenes:  # Pixabay takviye
        clips += fetch_pixabay_clips(themes, os.path.join(work, "pixa_amb"),
                                     count=scenes - len(clips), vertical=vertical)
    scene_files = []
    if clips:
        for i, c in enumerate(clips):
            s = _scene_from_clip(c, os.path.join(work, f"scn_{i}.mp4"), scene_sec, W, H, vertical)
            if s:
                scene_files.append(s)
    if not scene_files:
        src = "pollinations"
        prompts = [f"{t}, cinematic, dark moody, calming, ultra detailed, no text" for t in themes]
        imgs = fetch_pollinations_images(prompts, os.path.join(work, "amb_imgs"), vertical=vertical)
        for i, im in enumerate(imgs):
            s = _scene_from_image(im, os.path.join(work, f"scn_{i}.mp4"), scene_sec, W, H)
            if s:
                scene_files.append(s)
    if not scene_files:
        return {"success": False, "error": "ambient kaynak alınamadı (Pexels key veya ağ)"}

    # 2. Crossfade montaj (temel döngü) → süreye stream_loop ile döngüle
    base = os.path.join(work, "ambient_base.mp4")
    _xfade_concat(scene_files, base, xfade, scene_sec)
    if not os.path.exists(base):
        return {"success": False, "error": "crossfade montaj başarısız"}
    if not loop:
        if os.path.abspath(base) != os.path.abspath(out_path):
            subprocess.run(["ffmpeg", "-y", "-i", base, "-c", "copy", out_path], capture_output=True, timeout=120)
        return {"success": True, "path": out_path if os.path.exists(out_path) else base,
                "source": src, "scenes": len(scene_files), "looped": False}
    subprocess.run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", base, "-t", str(duration_sec),
                    "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", out_path],
                   capture_output=True, timeout=1800)
    if os.path.exists(out_path):
        return {"success": True, "path": out_path, "source": src, "scenes": len(scene_files), "looped": True}
    return {"success": False, "error": "süre döngüleme başarısız"}
