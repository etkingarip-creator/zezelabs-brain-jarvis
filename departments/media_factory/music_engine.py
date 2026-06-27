"""
Music Engine — ACE-Step (yerel, ücretsiz Suno alternatifi) ile GERÇEK müzik + şarkı/vokal.

ACE-Step FastAPI'sine (varsayılan http://localhost:8001) bağlanır. %100 yerel.
Akış: POST /release_task (prompt+lyrics+duration) → task_id → POST /query_result (poll)
→ first_audio_path → kopyala. Çalışmıyorsa None → çağıran sentez yatağa düşer.

Kurulum: ACE-Step 1.5 portable (C:\\ACE-Step-1.5), sunucu:
  python_embeded\\python acestep\\api_server.py --host 127.0.0.1 --port 8001 --download-source auto
"""
from __future__ import annotations
import os
import time
import json
import shutil
from typing import Optional


def _base() -> str:
    return os.getenv("ACESTEP_API_URL", "http://localhost:8001")


def is_available(timeout: float = 3.0) -> bool:
    """ACE-Step sunucusu ayakta + sağlıklı mı (/health)."""
    try:
        import requests
        r = requests.get(_base() + "/health", timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def generate_music(prompt: str, output_path: str, duration: int = 30,
                   lyrics: Optional[str] = None, poll_timeout: int = 300) -> Optional[str]:
    """ACE-Step ile gerçek müzik/şarkı üret.
    prompt=tarz/mood (örn 'upbeat cheerful kids song, ukulele'), lyrics=şarkı sözü (boş=enstrümantal).
    Döner: dosya yolu veya None."""
    if not is_available():
        return None
    try:
        import requests
    except Exception:
        return None
    try:
        body = {"prompt": prompt, "lyrics": lyrics or "", "audio_duration": float(duration)}
        r = requests.post(_base() + "/release_task", json=body, timeout=30)
        if r.status_code != 200:
            return None
        env = r.json().get("data", {}) if isinstance(r.json(), dict) else {}
        task_id = env.get("task_id")
        if not task_id:
            return None

        deadline = time.time() + poll_timeout
        while time.time() < deadline:
            time.sleep(8)
            q = requests.post(_base() + "/query_result",
                              json={"task_id_list": [task_id]}, timeout=30)
            if q.status_code != 200:
                continue
            try:
                items = q.json().get("data", [])
            except Exception:
                continue
            for it in (items if isinstance(items, list) else [items]):
                if not isinstance(it, dict):
                    continue
                # 'result' iç içe JSON string: [{"file": path, "wave": ..., "stage": ...}]
                res = it.get("result")
                inner = []
                if isinstance(res, str):
                    try:
                        inner = json.loads(res)
                    except Exception:
                        inner = []
                elif isinstance(res, list):
                    inner = res
                for seg in (inner if isinstance(inner, list) else [inner]):
                    if isinstance(seg, dict):
                        path = seg.get("file") or seg.get("wave")
                        if not path:
                            continue
                        path = str(path)
                        # ACE-Step 'file' tamamlanınca /v1/audio?path=... URL'i döner
                        if path.startswith("/v1/audio") or path.startswith("http"):
                            url = path if path.startswith("http") else _base() + path
                            dl = requests.get(url, timeout=120)
                            if dl.status_code == 200 and dl.content:
                                with open(output_path, "wb") as f:
                                    f.write(dl.content)
                                return output_path
                        elif os.path.exists(path):
                            shutil.copy(path, output_path)
                            return output_path
        return None
    except Exception:
        return None
