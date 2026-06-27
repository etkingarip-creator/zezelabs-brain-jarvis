"""
XTTS-v2 Sunucusu — doğal çok-dilli (EN+TR) seslendirme (Coqui XTTS-v2, yerel, ücretsiz).

C:\\xtts-env (Python 3.11 + CUDA) içinde çalışır. Modeli BİR KEZ yükler, port 8002'de
FastAPI ile sunar. POST /tts {text, language, speaker, out_path} → wav.

Başlat: C:\\xtts-env\\Scripts\\python.exe tools\\xtts_server.py
"""
import os
import torch
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

os.environ["COQUI_TOS_AGREED"] = "1"  # XTTS lisans onayı (non-interactive)

app = FastAPI()
_tts = None
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# Doğal anlatıcı varsayılan konuşmacılar (XTTS-v2 built-in)
DEFAULT_SPEAKER = os.getenv("XTTS_SPEAKER", "Damien Black")


def _model():
    global _tts
    if _tts is None:
        from TTS.api import TTS
        _tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(DEVICE)
    return _tts


class TTSReq(BaseModel):
    text: str
    language: str = "tr"        # tr | en
    speaker: str = ""           # boş → DEFAULT_SPEAKER
    out_path: str
    speaker_wav: str = ""       # ses klonlama için referans wav (opsiyonel)


@app.get("/health")
def health():
    return {"status": "ok", "device": DEVICE, "loaded": _tts is not None}


@app.get("/speakers")
def speakers():
    try:
        return {"speakers": list(getattr(_model().synthesizer.tts_model, "speaker_manager").name_to_id.keys())[:60]}
    except Exception as e:
        return {"error": str(e)}


@app.post("/tts")
def tts(req: TTSReq):
    try:
        m = _model()
        kwargs = {"text": req.text, "language": req.language, "file_path": req.out_path}
        if req.speaker_wav and os.path.exists(req.speaker_wav):
            kwargs["speaker_wav"] = req.speaker_wav   # kullanıcı sesini klonla
        else:
            kwargs["speaker"] = req.speaker or DEFAULT_SPEAKER
        m.tts_to_file(**kwargs)
        ok = os.path.exists(req.out_path) and os.path.getsize(req.out_path) > 0
        return {"ok": ok, "out_path": req.out_path}
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    _model()  # önceden yükle
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("XTTS_PORT", "8002")))
