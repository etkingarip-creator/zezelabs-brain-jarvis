"""
B-roll + Altyazı Görsel Motoru — profesyonel faceless stack (ücretsiz).

- Pexels API (ücretsiz) ile konuya uygun gerçek stok video b-roll çek.
- faster-whisper ile sesi transkribe et → senkron animasyonlu ASS altyazı.
- ffmpeg: b-roll sahnelerini ses süresine döngüle + altyazı yak + başlık + NotebookLM sesi.

Pexels key yoksa → Pollinations (key'siz AI görsel) yedeği.
"""
from __future__ import annotations
import os
import re
import json
import math
import subprocess
import urllib.request
import urllib.parse
from typing import List, Optional, Dict

_TIMEOUT = 60
_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def _download(url: str, dst: str, headers: Optional[dict] = None) -> bool:
    """UA header'lı güvenli indirme (urlretrieve UA göndermez → 403)."""
    h = {"User-Agent": _UA}
    if headers:
        h.update(headers)
    try:
        req = urllib.request.Request(url, headers=h)
        data = urllib.request.urlopen(req, timeout=_TIMEOUT).read()
        with open(dst, "wb") as f:
            f.write(data)
        return os.path.getsize(dst) > 5000
    except Exception:
        return False


def _ffprobe_duration(path: str) -> float:
    try:
        r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                            "-of", "default=noprint_wrappers=1:nokey=1", path],
                           capture_output=True, text=True, timeout=30)
        return float(r.stdout.strip())
    except Exception:
        return 0.0


# ---------- Pexels b-roll ----------
def fetch_pexels_clips(keywords: List[str], out_dir: str, count: int = 8,
                       vertical: bool = False, api_key: str = "") -> List[str]:
    """Anahtar kelimelere göre Pexels'ten dikey/yatay stok video indir."""
    api_key = api_key or os.getenv("PEXELS_API_KEY", "").strip()
    if not api_key:
        return []
    os.makedirs(out_dir, exist_ok=True)
    orient = "portrait" if vertical else "landscape"
    paths: List[str] = []
    per_kw = max(1, math.ceil(count / max(1, len(keywords))))
    for kw in keywords:
        if len(paths) >= count:
            break
        try:
            url = ("https://api.pexels.com/videos/search?query=" + urllib.parse.quote(kw) +
                   f"&orientation={orient}&per_page={per_kw}&size=medium")
            req = urllib.request.Request(url, headers={"Authorization": api_key})
            data = json.loads(urllib.request.urlopen(req, timeout=_TIMEOUT).read().decode())
            for vid in data.get("videos", []):
                files = sorted([f for f in vid.get("video_files", []) if f.get("width")],
                               key=lambda f: abs((f.get("height") or 0) - (1920 if vertical else 1080)))
                if not files:
                    continue
                link = files[0]["link"]
                dst = os.path.join(out_dir, f"broll_{len(paths)}.mp4")
                if _download(link, dst):
                    paths.append(dst)
                if len(paths) >= count:
                    break
        except Exception:
            continue
    return paths


# ---------- Pollinations yedeği (key'siz AI görsel) ----------
def fetch_pollinations_images(prompts: List[str], out_dir: str, vertical: bool = False) -> List[str]:
    os.makedirs(out_dir, exist_ok=True)
    w, h = (1080, 1920) if vertical else (1920, 1080)
    paths = []
    for i, pr in enumerate(prompts):
        try:
            url = (f"https://image.pollinations.ai/prompt/{urllib.parse.quote(pr[:300])}"
                   f"?width={w}&height={h}&nologo=true&seed={i*7+3}")
            dst = os.path.join(out_dir, f"img_{i}.jpg")
            if _download(url, dst):
                paths.append(dst)
        except Exception:
            continue
    return paths


# ---------- Whisper altyazı ----------
def transcribe_to_ass(audio_path: str, ass_path: str, vertical: bool = False,
                      max_words: int = 6) -> bool:
    """faster-whisper ile transkribe → animasyonlu ASS altyazı (kelime grupları)."""
    try:
        from faster_whisper import WhisperModel
    except Exception:
        return False
    try:
        model = WhisperModel("base", device="cuda", compute_type="float16")
    except Exception:
        try:
            model = WhisperModel("base", device="cpu", compute_type="int8")
        except Exception:
            return False
    try:
        segments, _ = model.transcribe(audio_path, word_timestamps=True, vad_filter=True)
        play_w, play_h = (1080, 1920) if vertical else (1920, 1080)
        fs = 64 if vertical else 52
        margin_v = 320 if vertical else 90
        lines = [
            "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {play_w}", f"PlayResY: {play_h}", "",
            "[V4+ Styles]",
            "Format: Name,Fontname,Fontsize,PrimaryColour,OutlineColour,BackColour,Bold,Italic,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
            f"Style: Cap,Arial Black,{fs},&H00FFFFFF,&H00000000,&H80000000,1,0,1,4,2,2,60,60,{margin_v},1",
            "", "[Events]",
            "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text",
        ]

        def t(sec):
            h = int(sec // 3600); m = int((sec % 3600) // 60); s = sec % 60
            return f"{h:d}:{m:02d}:{s:05.2f}"

        buf = []
        for seg in segments:
            words = getattr(seg, "words", None) or []
            for wd in words:
                buf.append((wd.start, wd.end, wd.word.strip()))
                if len(buf) >= max_words:
                    st, en = buf[0][0], buf[-1][1]
                    txt = " ".join(w[2] for w in buf).replace("\n", " ")
                    lines.append(f"Dialogue: 0,{t(st)},{t(en)},Cap,,0,0,0,,{txt}")
                    buf = []
        if buf:
            st, en = buf[0][0], buf[-1][1]
            txt = " ".join(w[2] for w in buf)
            lines.append(f"Dialogue: 0,{t(st)},{t(en)},Cap,,0,0,0,,{txt}")
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return True
    except Exception:
        return False


# ---------- Montaj ----------
def _image_to_clip(img: str, out: str, sec: float, W: int, H: int) -> Optional[str]:
    """Görseli yavaş Ken Burns'lü video sahnesine çevir."""
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"zoompan=z='min(zoom+0.0008,1.15)':d={int(sec*30)}:s={W}x{H}:fps=30,setsar=1")
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", img, "-t", str(sec),
                    "-vf", vf, "-c:v", "libx264", "-preset", "veryfast",
                    "-pix_fmt", "yuv420p", out], capture_output=True, timeout=120)
    return out if os.path.exists(out) and os.path.getsize(out) > 5000 else None


def assemble_rich(audio_path: str, output_path: str, keywords: List[str],
                  image_prompts: Optional[List[str]] = None, title: str = "",
                  vertical: bool = False, captions: bool = True) -> Dict:
    """Tam zengin montaj: b-roll (Pexels) veya AI görsel (Pollinations) + Whisper altyazı + ses."""
    work = os.path.dirname(output_path)
    os.makedirs(work, exist_ok=True)
    W, H = (1080, 1920) if vertical else (1920, 1080)
    src = "pexels"
    clips = fetch_pexels_clips(keywords, os.path.join(work, "pexels"), count=10, vertical=vertical)
    if not clips:
        # key yok → Pollinations AI görsel → klip
        src = "pollinations"
        prompts = image_prompts or [f"{k}, cinematic, high detail, professional" for k in keywords]
        imgs = fetch_pollinations_images(prompts, os.path.join(work, "imgs"), vertical=vertical)
        clips = []
        for i, im in enumerate(imgs):
            c = _image_to_clip(im, os.path.join(work, f"imgclip_{i}.mp4"), 6.0, W, H)
            if c:
                clips.append(c)
    if not clips:
        return {"success": False, "error": "ne Pexels ne Pollinations görsel alınamadı", "source": src}
    ass = None
    if captions:
        ass = os.path.join(work, "captions.ass")
        if not transcribe_to_ass(audio_path, ass, vertical=vertical):
            ass = None
    out = build_broll_video(audio_path, output_path, clips, title=title, ass_path=ass, vertical=vertical)
    if out:
        return {"success": True, "path": out, "visual_source": src,
                "captions": bool(ass), "clip_count": len(clips)}
    return {"success": False, "error": "montaj başarısız", "source": src}


def build_broll_video(audio_path: str, output_path: str, clips: List[str],
                      title: str = "", ass_path: Optional[str] = None,
                      vertical: bool = False, scene_sec: float = 6.0) -> Optional[str]:
    """B-roll sahnelerini ses süresine döngüle, altyazı+başlık yak, NotebookLM sesini kullan."""
    dur = _ffprobe_duration(audio_path)
    if dur <= 0 or not clips:
        return None
    work = os.path.dirname(output_path)
    W, H = (1080, 1920) if vertical else (1920, 1080)
    # 1. Her klibi sabit süreye normalize et (scale+crop+trim, sessiz)
    norm = []
    for i, c in enumerate(clips):
        n = os.path.join(work, f"norm_{i}.mp4")
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"setsar=1,fps=30")
        r = subprocess.run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", c, "-t", str(scene_sec),
                            "-an", "-vf", vf, "-c:v", "libx264", "-preset", "veryfast",
                            "-pix_fmt", "yuv420p", n], capture_output=True, timeout=180)
        if os.path.exists(n) and os.path.getsize(n) > 5000:
            norm.append(n)
    if not norm:
        return None
    # 2. Süreyi doldurana kadar sahneleri sırayla tekrarla → concat listesi
    need = math.ceil(dur / scene_sec)
    seq = [norm[i % len(norm)] for i in range(need)]
    lst = os.path.join(work, "concat.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for s in seq:
            f.write(f"file '{os.path.abspath(s)}'\n")
    bg = os.path.join(work, "broll_bg.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-t", str(dur), "-c", "copy", bg], capture_output=True, timeout=300)
    if not os.path.exists(bg):
        return None
    # 3. Altyazı + başlık yak, NotebookLM sesini bindir
    vf_parts = []
    if ass_path and os.path.exists(ass_path):
        vf_parts.append("subtitles='" + ass_path.replace("\\", "/").replace(":", "\\:") + "'")
    if title:
        safe = title.replace("'", "").replace(":", " -")
        y = 150 if vertical else 90
        vf_parts.append(f"drawtext=text='{safe}':fontcolor=white:fontsize={56 if not vertical else 60}:"
                        f"x=(w-text_w)/2:y={y}:box=1:boxcolor=black@0.55:boxborderw=18:enable='lt(t,6)'")
    vf = ",".join(vf_parts) if vf_parts else "null"
    cmd = ["ffmpeg", "-y", "-i", bg, "-i", audio_path,
           "-vf", vf, "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", output_path]
    subprocess.run(cmd, capture_output=True, timeout=900)
    return output_path if os.path.exists(output_path) else None
