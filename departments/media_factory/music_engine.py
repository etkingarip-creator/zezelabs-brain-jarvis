"""
Music Engine — ACE-Step (yerel, ücretsiz Suno alternatifi) ile GERÇEK müzik + şarkı/vokal.

ACE-Step 1.5 Gradio API'sine (varsayılan http://localhost:8001) bağlanır. %100 yerel,
6GB VRAM'e sığar (PT backend ~1.6GB). Çalışmıyorsa None döner → çağıran sentez yatağa düşer.

Kurulum (kullanıcı):
  1. ACE-Step 1.5 kur (acestep) + bu repo: github.com/fspecii/ace-step-ui
  2. Gradio sunucu: acestep --port 8001 --enable-api
  3. ACESTEP_API_URL=http://localhost:8001 (varsayılan)
"""
from __future__ import annotations
import os
from typing import Optional


def _api_url() -> str:
    return os.getenv("ACESTEP_API_URL", "http://localhost:8001")


def is_available(timeout: float = 3.0) -> bool:
    """ACE-Step Gradio sunucusu ayakta mı?"""
    try:
        import requests
        r = requests.get(_api_url(), timeout=timeout)
        return r.status_code < 500
    except Exception:
        return False


def generate_music(prompt: str, output_path: str, duration: int = 30,
                   lyrics: Optional[str] = None, api_name: Optional[str] = None) -> Optional[str]:
    """ACE-Step ile gerçek müzik/şarkı üret. prompt=tarz/mood (örn 'upbeat cheerful kids song,
    ukulele, claps'), lyrics=şarkı sözü (vokal için). Döner: dosya yolu veya None.
    gradio API imzası sürümle değişebilir → ACESTEP_API_NAME ile override edilebilir."""
    if not is_available():
        return None
    try:
        from gradio_client import Client
    except Exception:
        return None
    try:
        client = Client(_api_url())
        name = api_name or os.getenv("ACESTEP_API_NAME", "/generate")
        # ACE-Step tipik girdiler: (prompt/tags, lyrics, duration). İmza değişirse env ile ayarla.
        try:
            result = client.predict(prompt, lyrics or "", float(duration), api_name=name)
        except Exception:
            # alternatif imza (yalnız prompt + süre)
            result = client.predict(prompt, float(duration), api_name=name)
        # result genelde dosya yolu (veya {"name": path}) döner
        src = result.get("name") if isinstance(result, dict) else (
            result[0] if isinstance(result, (list, tuple)) else result)
        if src and os.path.exists(str(src)):
            import shutil
            shutil.copy(str(src), output_path)
            return output_path
        return None
    except Exception:
        return None
