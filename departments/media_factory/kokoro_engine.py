"""
Kokoro TTS Client — yerel, ücretsiz, TİCARİ (Apache 2.0), hızlı (~9x gerçek-zaman, GPU).

media_factory'nin BİRİNCİL seslendirme motoru (ElevenLabs/XTTS yerine):
- Ticari kullanım serbest (Apache 2.0) → monetize içerikte güvenli.
- Hızlı → 2-4 saat uyku videosu dakikalarda, $0.
Sunucu: C:\\xtts-env\\Scripts\\python.exe tools\\kokoro_server.py (port 8003).
Kapalıysa None → çağıran edge-tts'e düşer.
"""
from __future__ import annotations
import os
import re
import tempfile
import subprocess
from typing import Optional, List

# İçerik tipine göre ses: anlatım sıcak kadın (af_heart), erkek alternatif (am_michael)
DEFAULT_VOICE = "af_heart"


def _base() -> str:
    return os.getenv("KOKORO_API_URL", "http://localhost:8003")


def is_available(timeout: float = 3.0) -> bool:
    try:
        import requests
        return requests.get(_base() + "/health", timeout=timeout).status_code == 200
    except Exception:
        return False


def _chunk(text: str, max_chars: int = 1800) -> List[str]:
    """Kokoro uzun metni kendi içinde böler; yine de çok uzun istekleri paragraf/cümlede parçala."""
    text = (text or "").strip()
    if len(text) <= max_chars:
        return [text] if text else []
    sents = re.split(r"(?<=[.!?])\s+", text)
    chunks, cur = [], ""
    for s in sents:
        if cur and len(cur) + len(s) + 1 > max_chars:
            chunks.append(cur); cur = s
        else:
            cur = (cur + " " + s).strip()
    if cur:
        chunks.append(cur)
    return [c for c in chunks if c.strip()]


def synth(text: str, out_path: str, lang: str = "en", voice: str = "",
          speed: float = 1.0, poll_timeout: int = 1800) -> Optional[str]:
    """Kokoro ile seslendirme. lang: a/en(American), b(British)... voice: af_heart vb.
    Uzun metin parçalanır, birleştirilir. Sleep için speed=0.92 önerilir (sakin)."""
    if not is_available():
        return None
    try:
        import requests
    except Exception:
        return None
    lang_code = {"en": "a", "en-us": "a", "en-gb": "b"}.get(lang.lower(), lang if len(lang) == 1 else "a")
    voice = voice or DEFAULT_VOICE
    work = tempfile.mkdtemp(prefix="kokoro_")
    parts = []
    try:
        for i, ch in enumerate(_chunk(text)):
            wp = os.path.join(work, f"p{i}.wav")
            r = requests.post(_base() + "/tts",
                              json={"text": ch, "voice": voice, "lang": lang_code,
                                    "out_path": wp, "speed": speed},
                              timeout=poll_timeout)
            if r.status_code == 200 and r.json().get("success") and os.path.exists(wp):
                parts.append(wp)
        if not parts:
            return None
        if len(parts) == 1 and out_path.lower().endswith(".wav"):
            import shutil; shutil.copy(parts[0], out_path); return out_path
        lst = os.path.join(work, "list.txt")
        with open(lst, "w", encoding="utf-8") as f:
            f.write("".join(f"file '{p}'\n" for p in parts))
        codec = ["-c:a", "libmp3lame", "-q:a", "2"] if not out_path.lower().endswith(".wav") else []
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst] + codec + [out_path],
                       capture_output=True, timeout=300)
        return out_path if os.path.exists(out_path) and os.path.getsize(out_path) > 0 else None
    except Exception:
        return None
    finally:
        try:
            import shutil; shutil.rmtree(work, ignore_errors=True)
        except Exception:
            pass
