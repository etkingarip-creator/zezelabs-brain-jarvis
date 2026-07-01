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
            req = urllib.request.Request(url, headers={"Authorization": api_key, "User-Agent": _UA})
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


# ---------- Pexels FOTO (thumbnail için yüksek-çöz. dolu özne) ----------
def fetch_pexels_photos(keywords: List[str], out_dir: str, count: int = 3,
                        vertical: bool = False, api_key: str = "") -> List[str]:
    """Thumbnail arka planı için yüksek-çözünürlüklü Pexels fotoğrafı (dolu/merkezi özne)."""
    api_key = api_key or os.getenv("PEXELS_API_KEY", "").strip()
    if not api_key:
        return []
    os.makedirs(out_dir, exist_ok=True)
    orient = "portrait" if vertical else "landscape"
    paths: List[str] = []
    for kw in keywords:
        if len(paths) >= count:
            break
        try:
            url = ("https://api.pexels.com/v1/search?query=" + urllib.parse.quote(kw) +
                   f"&orientation={orient}&per_page=5&size=large")
            req = urllib.request.Request(url, headers={"Authorization": api_key, "User-Agent": _UA})
            data = json.loads(urllib.request.urlopen(req, timeout=_TIMEOUT).read().decode())
            for ph in data.get("photos", []):
                link = (ph.get("src", {}).get("large2x") or ph.get("src", {}).get("original")
                        or ph.get("src", {}).get("large"))
                if not link:
                    continue
                dst = os.path.join(out_dir, f"photo_{len(paths)}.jpg")
                if _download(link, dst):
                    paths.append(dst)
                if len(paths) >= count:
                    break
        except Exception:
            continue
    return paths


# ---------- Pixabay b-roll (Pexels yedeği/takviyesi) ----------
def fetch_pixabay_clips(keywords: List[str], out_dir: str, count: int = 8,
                        vertical: bool = False, api_key: str = "") -> List[str]:
    """Pixabay ücretsiz stok video (Pexels yetmezse takviye)."""
    api_key = api_key or os.getenv("PIXABAY_API_KEY", "").strip()
    if not api_key:
        return []
    os.makedirs(out_dir, exist_ok=True)
    paths: List[str] = []
    per_kw = max(1, math.ceil(count / max(1, len(keywords))))
    for kw in keywords:
        if len(paths) >= count:
            break
        try:
            url = ("https://pixabay.com/api/videos/?key=" + urllib.parse.quote(api_key) +
                   "&q=" + urllib.parse.quote(kw) + f"&per_page={max(3, per_kw)}&safesearch=true")
            req = urllib.request.Request(url, headers={"User-Agent": _UA})
            data = json.loads(urllib.request.urlopen(req, timeout=_TIMEOUT).read().decode())
            for hit in data.get("hits", []):
                vids = hit.get("videos", {})
                f = vids.get("large") or vids.get("medium") or vids.get("small")
                if not f or not f.get("url"):
                    continue
                dst = os.path.join(out_dir, f"pixa_{len(paths)}.mp4")
                if _download(f["url"], dst):
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
def _transcribe(audio_path: str):
    """faster-whisper transkripsiyon → segment listesi (word_timestamps). CUDA→CPU düş."""
    try:
        from faster_whisper import WhisperModel
    except Exception:
        return None
    for dev, ct in [("cuda", "float16"), ("cpu", "int8")]:
        try:
            model = WhisperModel("base", device=dev, compute_type=ct)
            segs, _ = model.transcribe(audio_path, word_timestamps=True, vad_filter=True)
            return list(segs)  # cublas hatası burada patlar → CPU'ya düşer
        except Exception:
            continue
    return None


def _srt_time(sec: float) -> str:
    h = int(sec // 3600); m = int((sec % 3600) // 60); s = int(sec % 60); ms = int((sec - int(sec)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(segments, srt_path: str) -> bool:
    """Segment-bazlı SRT (YouTube'a soft caption olarak yüklenir — SEO + çeviri)."""
    if not segments:
        return False
    try:
        out = []
        for i, seg in enumerate(segments, 1):
            txt = (getattr(seg, "text", "") or "").strip()
            if not txt:
                continue
            out.append(str(i))
            out.append(f"{_srt_time(seg.start)} --> {_srt_time(seg.end)}")
            out.append(txt)
            out.append("")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(out))
        return True
    except Exception:
        return False


def make_captions(audio_path: str, ass_path: Optional[str] = None,
                  srt_path: Optional[str] = None, vertical: bool = False,
                  max_words: int = 6) -> Dict:
    """Tek transkripsiyon → istenen formatlar. ass=dikey yakılı, srt=uzun-form YouTube soft."""
    segments = _transcribe(audio_path)
    if not segments:
        return {"ass": False, "srt": False}
    res = {"ass": False, "srt": False}
    if srt_path:
        res["srt"] = write_srt(segments, srt_path)
    if ass_path:
        res["ass"] = _write_ass(segments, ass_path, vertical=vertical, max_words=max_words)
    return res


def transcribe_to_ass(audio_path: str, ass_path: str, vertical: bool = False,
                      max_words: int = 6) -> bool:
    """Geriye-uyumluluk: tek seferde transkribe + ASS yaz."""
    segments = _transcribe(audio_path)
    if not segments:
        return False
    return _write_ass(segments, ass_path, vertical=vertical, max_words=max_words)


def _write_ass(segments, ass_path: str, vertical: bool = False, max_words: int = 6) -> bool:
    """Animasyonlu ASS altyazı (kelime grupları, metin hiyerarşisi)."""
    try:
        play_w, play_h = (1080, 1920) if vertical else (1920, 1080)
        # Metin hiyerarşisi: kalın, güçlü stroke+gölge, alt-üçlük. Dikeyde daha küçük + az kelime (taşmasın).
        fs = 56 if vertical else 60
        margin_v = 380 if vertical else 130
        if vertical:
            max_words = min(max_words, 4)  # dikeyde satır dar → 4 kelime sığar
        lines = [
            "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {play_w}", f"PlayResY: {play_h}",
            "WrapStyle: 2", "",
            "[V4+ Styles]",
            "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
            # PrimaryColour beyaz, Outline siyah kalın(5), Shadow(3). Alignment 2 = alt-orta.
            f"Style: Cap,Arial Black,{fs},&H00FFFFFF,&H0000FFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,5,3,2,80,80,{margin_v},1",
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
                  vertical: bool = False, captions: bool = True,
                  burn_captions: Optional[bool] = None, intro_clip: Optional[str] = None) -> Dict:
    """Tam zengin montaj: b-roll/AI görsel + Whisper altyazı + ses.
    burn_captions: None→dikeyde yak, uzun-formda yakma (SRT üret). Açık verilirse onu uygular.
    Uzun-form için SRT döner (YouTube'a soft caption yüklenir → SEO+çeviri)."""
    work = os.path.dirname(output_path)
    os.makedirs(work, exist_ok=True)
    W, H = (1080, 1920) if vertical else (1920, 1080)
    src = "pexels"
    clips = fetch_pexels_clips(keywords, os.path.join(work, "pexels"), count=10, vertical=vertical)
    if len(clips) < 6:  # Pixabay ile takviye
        more = fetch_pixabay_clips(keywords, os.path.join(work, "pixabay"), count=10 - len(clips), vertical=vertical)
        if more:
            clips += more; src = "pexels+pixabay" if clips else src
    if not clips:
        # GERÇEK VİDEO yok → statik AI görsel "ilkokul seviyesi", kullanıcı istemiyor → dürüstçe başarısız.
        return {"success": False, "source": src,
                "error": "Gerçek stok video (Pexels/Pixabay) alınamadı. Statik görsele düşmüyoruz "
                         "(kalite çıtası). Pexels/Pixabay key veya ağ/limit kontrol et."}
    if burn_captions is None:
        burn_captions = vertical  # dikey=yak, uzun-form=yakma (soft SRT)
    ass = None
    srt = None
    if captions:
        ass_target = os.path.join(work, "captions.ass") if burn_captions else None
        srt_target = os.path.join(work, "captions.srt")  # her zaman üret (YouTube soft upload)
        cap = make_captions(audio_path, ass_path=ass_target, srt_path=srt_target, vertical=vertical)
        ass = ass_target if cap.get("ass") else None
        srt = srt_target if cap.get("srt") else None
    out = build_broll_video(audio_path, output_path, clips, title=title, ass_path=ass,
                            vertical=vertical, intro_clip=intro_clip)
    if out:
        return {"success": True, "path": out, "visual_source": src,
                "burned_captions": bool(ass), "srt_path": srt, "clip_count": len(clips)}
    return {"success": False, "error": "montaj başarısız", "source": src}


def build_broll_video(audio_path: str, output_path: str, clips: List[str],
                      title: str = "", ass_path: Optional[str] = None,
                      vertical: bool = False, scene_sec: float = 6.0,
                      intro_clip: Optional[str] = None) -> Optional[str]:
    """B-roll sahnelerini ses süresine döngüle, altyazı+başlık yak, NotebookLM sesini kullan."""
    dur = _ffprobe_duration(audio_path)
    if dur <= 0 or not clips:
        return None
    work = os.path.dirname(output_path)
    W, H = (1080, 1920) if vertical else (1920, 1080)
    # 1. Her klibi normalize + SİNEMATİK GRADE (kontrast/doygunluk + sıcak ton) + vignette
    grade = ("eq=contrast=1.09:saturation=1.18:brightness=-0.015,"
             "colorbalance=rs=0.03:bs=-0.03:gm=0.02,vignette=PI/5,unsharp=3:3:0.4")
    def _norm(src, n, slen):
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30,{grade}")
        subprocess.run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", src, "-t", str(slen), "-an", "-vf", vf,
                        "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", n],
                       capture_output=True, timeout=180)
        return n if os.path.exists(n) and os.path.getsize(n) > 5000 else None

    def _xfade(scenes, out, xf, slen):
        if len(scenes) == 1:
            subprocess.run(["ffmpeg", "-y", "-i", scenes[0], "-c", "copy", out], capture_output=True, timeout=120)
            return out
        cur, off = scenes[0], slen - xf
        for k in range(1, len(scenes)):
            nx = os.path.join(work, f"_xf{k}.mp4")
            fc = f"[0:v][1:v]xfade=transition=fade:duration={xf}:offset={off}[v]"
            subprocess.run(["ffmpeg", "-y", "-i", cur, "-i", scenes[k], "-filter_complex", fc, "-map", "[v]",
                            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", nx],
                           capture_output=True, timeout=600)
            if not (os.path.exists(nx) and os.path.getsize(nx) > 5000):
                return cur
            cur, off = nx, off + (slen - xf)
        return cur

    # 1. GÖVDE sahneleri (grade'li) → crossfade base
    norm = [r for i, c in enumerate(clips) if (r := _norm(c, os.path.join(work, f"norm_{i}.mp4"), scene_sec))]
    if not norm:
        return None
    base = _xfade(norm, os.path.join(work, "body_base.mp4"), 0.8, scene_sec)

    # 2. HİBRİT: HOOK (0-~12s hızlı kesim, enerjik) + GÖVDE (sakin crossfade, süreye döngü)
    hook_sec = 2.4
    hook_dur = min(12.0, dur * 0.18)
    hooks = [r for i in range(max(1, int(hook_dur / hook_sec)))
             if (r := _norm(clips[i % len(clips)], os.path.join(work, f"hook_{i}.mp4"), hook_sec))]
    hook_mp4 = os.path.join(work, "hook.mp4")
    if hooks:
        hl = os.path.join(work, "hooklist.txt")
        with open(hl, "w", encoding="utf-8") as f:
            f.write("".join(f"file '{os.path.abspath(h)}'\n" for h in hooks))
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", hl, "-c", "copy", hook_mp4],
                       capture_output=True, timeout=120)
    hook_real = hook_sec * len(hooks)
    body = os.path.join(work, "body.mp4")
    subprocess.run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", base, "-t", str(max(1.0, dur - hook_real)),
                    "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", body],
                   capture_output=True, timeout=900)
    bg = os.path.join(work, "broll_bg.mp4")
    if os.path.exists(hook_mp4) and os.path.exists(body) and hook_real > 1:
        fc = f"[0:v][1:v]xfade=transition=fade:duration=0.6:offset={max(0.1, hook_real - 0.6)}[v]"
        subprocess.run(["ffmpeg", "-y", "-i", hook_mp4, "-i", body, "-filter_complex", fc, "-map", "[v]",
                        "-t", str(dur), "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", bg],
                       capture_output=True, timeout=1200)
    if not os.path.exists(bg) and os.path.exists(body):
        subprocess.run(["ffmpeg", "-y", "-i", body, "-t", str(dur), "-c", "copy", bg], capture_output=True, timeout=300)
    if not os.path.exists(bg):
        return None
    # 2.5 Harita girişi (varsa) → bg'nin başına ekle, toplam = ses uzunluğu (anlatım intro üstünde çalar)
    if intro_clip and os.path.exists(intro_clip):
        intro_dur = min(_ffprobe_duration(intro_clip), 8.0)
        if intro_dur > 1:
            intro_n = os.path.join(work, "intro_norm.mp4")
            subprocess.run(["ffmpeg", "-y", "-i", intro_clip, "-t", str(intro_dur),
                            "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30",
                            "-an", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", intro_n],
                           capture_output=True, timeout=180)
            body_trim = os.path.join(work, "body_trim.mp4")
            subprocess.run(["ffmpeg", "-y", "-i", bg, "-t", str(max(1.0, dur - intro_dur)),
                            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", body_trim],
                           capture_output=True, timeout=300)
            il = os.path.join(work, "introcat.txt")
            with open(il, "w", encoding="utf-8") as f:
                f.write(f"file '{os.path.abspath(intro_n)}'\nfile '{os.path.abspath(body_trim)}'\n")
            merged = os.path.join(work, "with_intro.mp4")
            subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", il,
                            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", merged],
                           capture_output=True, timeout=300)
            if os.path.exists(merged) and os.path.getsize(merged) > 5000:
                bg = merged

    # 3. Altyazı + başlık yak, ses bindir
    vf_parts = []
    if ass_path and os.path.exists(ass_path):
        ap = ass_path.replace("\\", "/").replace(":", "\\:")
        vf_parts.append(f"subtitles='{ap}':fontsdir='C\\:/Windows/Fonts'")
    if title:
        safe = title.replace("'", "").replace(":", " -")
        y = 150 if vertical else 90
        ff = "C\\:/Windows/Fonts/arialbd.ttf"  # Windows fontconfig yok → açık font dosyası şart
        vf_parts.append(f"drawtext=fontfile='{ff}':text='{safe}':fontcolor=white:"
                        f"fontsize={56 if not vertical else 60}:x=(w-text_w)/2:y={y}:"
                        f"box=1:boxcolor=black@0.55:boxborderw=18:enable='lt(t,6)'")
    vf = ",".join(vf_parts) if vf_parts else "null"
    # Ses: loudnorm (YouTube -14 LUFS) + güvenli volume → kısık ses sorunu çözülür
    cmd = ["ffmpeg", "-y", "-i", bg, "-i", audio_path,
           "-vf", vf, "-map", "0:v", "-map", "1:a",
           "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,volume=1.5",
           "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", output_path]
    subprocess.run(cmd, capture_output=True, timeout=900)
    return output_path if os.path.exists(output_path) else None
