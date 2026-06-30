"""
Kokoro TTS Server — yerel, ücretsiz, TİCARİ (Apache 2.0), hızlı (GPU ~9x gerçek-zaman).
ElevenLabs/XTTS alternatifi. Python 3.11 ortamında çalışır (C:\\xtts-env).

Çalıştır: C:\\xtts-env\\Scripts\\python.exe tools\\kokoro_server.py
Port 8003. POST /tts {text, voice, lang, out_path}  ·  GET /health  ·  GET /voices
"""
import os
import time
import numpy as np
import soundfile as sf
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

LANG = "a"  # a=American English, b=British, e=Spanish, f=French, h=Hindi, i=Italian, p=Portuguese, j=Japanese, z=Chinese
DEFAULT_VOICE = "af_heart"
PORT = 8003

app = FastAPI(title="Kokoro TTS")
_pipelines = {}


def _get_pipeline(lang_code: str):
    if lang_code not in _pipelines:
        from kokoro import KPipeline
        import torch
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        try:
            _pipelines[lang_code] = KPipeline(lang_code=lang_code, device=dev)
        except Exception:
            _pipelines[lang_code] = KPipeline(lang_code=lang_code)
    return _pipelines[lang_code]


class TTSReq(BaseModel):
    text: str
    voice: str = DEFAULT_VOICE
    lang: str = LANG
    out_path: str
    speed: float = 1.0


@app.get("/health")
def health():
    import torch
    return {"status": "ok", "loaded": bool(_pipelines),
            "device": "cuda" if torch.cuda.is_available() else "cpu", "engine": "kokoro"}


@app.get("/voices")
def voices():
    # Kokoro yerleşik sesleri (a = American English en kaliteli olanlar)
    return {"american_female": ["af_heart", "af_bella", "af_nicole", "af_sarah", "af_sky"],
            "american_male": ["am_michael", "am_adam", "am_eric", "am_liam"],
            "british_female": ["bf_emma", "bf_isabella"], "british_male": ["bm_george", "bm_lewis"]}


@app.post("/tts")
def tts(req: TTSReq):
    t0 = time.time()
    pipe = _get_pipeline(req.lang or LANG)
    chunks = []
    for _, _, audio in pipe(req.text, voice=req.voice, speed=req.speed):
        chunks.append(audio)
    if not chunks:
        return {"success": False, "error": "ses üretilmedi"}
    au = np.concatenate(chunks)
    out = req.out_path
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    if out.lower().endswith(".wav"):
        sf.write(out, au, 24000)
    else:
        # mp3/diğer → önce wav, ffmpeg ile çevir
        wav = out + ".tmp.wav"
        sf.write(wav, au, 24000)
        import subprocess
        subprocess.run(["ffmpeg", "-y", "-i", wav, out], capture_output=True, timeout=300)
        try:
            os.remove(wav)
        except Exception:
            pass
    dur = len(au) / 24000
    return {"success": True, "path": out, "duration_sec": round(dur, 1),
            "gen_sec": round(time.time() - t0, 1)}


if __name__ == "__main__":
    print(f"[Kokoro] Yükleniyor (port {PORT})...")
    _get_pipeline(LANG)
    print("[Kokoro] Hazır.")
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
