"""
TTS Engine — doğal çok-dilli seslendirme (XTTS-v2 sunucusu, yerel ücretsiz).

XTTS-v2 (Coqui) sunucusuna (localhost:8002) bağlanır — EN+TR doğal, insan-gibi, ses
klonlama destekli. Uzun metni cümle/paragraf parçalar, sentezler, ffmpeg ile birleştirir.
Sunucu kapalıysa None → çağıran edge-tts'e düşer (graceful).

Sunucu: C:\\xtts-env\\Scripts\\python.exe tools\\xtts_server.py  (port 8002)
"""
from __future__ import annotations
import os
import re
import tempfile
import subprocess
from typing import Optional, List


def _base() -> str:
    return os.getenv("XTTS_API_URL", "http://localhost:8002")


def is_available(timeout: float = 3.0) -> bool:
    try:
        import requests
        return requests.get(_base() + "/health", timeout=timeout).status_code == 200
    except Exception:
        return False


def _chunk(text: str, max_chars: int = 180) -> List[str]:
    """Cümle sınırında parçala. KÜÇÜK tut (XTTS token limiti aşılırsa CUDA index assert →
    context bozulur). Uzun cümleleri virgül/boşlukla da böl."""
    text = (text or "").strip()
    raw = re.split(r"(?<=[.!?])\s+", text)
    sents = []
    for s in raw:
        if len(s) <= max_chars:
            sents.append(s)
        else:  # uzun cümleyi virgül/kelime ile parçala
            cur = ""
            for part in re.split(r"(?<=[,;:])\s+", s):
                if cur and len(cur) + len(part) + 1 > max_chars:
                    sents.append(cur); cur = part
                else:
                    cur = (cur + " " + part).strip()
            if cur:
                sents.append(cur)
    chunks, cur = [], ""
    for s in sents:
        if cur and len(cur) + len(s) + 1 > max_chars:
            chunks.append(cur); cur = s
        else:
            cur = (cur + " " + s).strip()
    if cur:
        chunks.append(cur)
    return [c for c in chunks if c.strip()] or [text[:max_chars]]


def synth(text: str, out_path: str, lang: str = "tr", speaker: str = "",
          speaker_wav: str = "", poll_timeout: int = 600) -> Optional[str]:
    """XTTS-v2 ile doğal seslendirme. lang: tr|en. speaker_wav: ses klonlama referansı (ops).
    Uzun metin parçalanır, her parça sentezlenir, birleştirilir."""
    if not is_available():
        return None
    try:
        import requests
    except Exception:
        return None
    work = tempfile.mkdtemp(prefix="xtts_")
    parts = []
    try:
        for i, ch in enumerate(_chunk(text)):
            wp = os.path.join(work, f"p{i}.wav")
            r = requests.post(_base() + "/tts",
                              json={"text": ch, "language": lang, "speaker": speaker,
                                    "speaker_wav": speaker_wav, "out_path": wp},
                              timeout=poll_timeout)
            if r.status_code == 200 and r.json().get("ok") and os.path.exists(wp):
                parts.append(wp)
        if not parts:
            return None
        lst = os.path.join(work, "list.txt")
        with open(lst, "w", encoding="utf-8") as f:
            f.write("".join(f"file '{p}'\n" for p in parts))
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                        "-c:a", "libmp3lame", "-q:a", "2", out_path],
                       capture_output=True, timeout=180)
        return out_path if os.path.exists(out_path) and os.path.getsize(out_path) > 0 else None
    except Exception:
        return None
    finally:
        try:
            import shutil; shutil.rmtree(work, ignore_errors=True)
        except Exception:
            pass
