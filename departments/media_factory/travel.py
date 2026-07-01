"""
Travel Shorts — destinasyon anlatımı + eşleşen gerçek stok footage + travel-affiliate.

Avantaj: destinasyon ADI = mükemmel stok arama terimi → görsel anlatımla birebir eşleşir.
Tamamen mevcut stack: Kokoro ses + Pexels/Pixabay footage + Whisper altyazı + MrBeast kapak +
seo_metadata + bu dosyadaki travel-affiliate config.
"""
from __future__ import annotations
import re
import json
from typing import List, Dict

# Travel affiliate programları (yüksek komisyon + tekrarlayan/hacim). URL'ler placeholder →
# kullanıcı kendi affiliate ID'siyle doldurur (env/config). ZORUNLU: gerçek link gelene kadar sahte gelir yok.
TRAVEL_AFFILIATES = [
    {"name": "Booking.com (otel)", "url": "", "note": "konaklama — yüksek hacim"},
    {"name": "GetYourGuide (tur/aktivite)", "url": "", "note": "tur & bilet — yüksek komisyon"},
    {"name": "Skyscanner (uçak)", "url": "", "note": "uçuş karşılaştırma"},
    {"name": "Airalo (eSIM)", "url": "", "note": "seyahat interneti — tekrarlayan"},
    {"name": "Viator (gezi)", "url": "", "note": "aktivite rezervasyon"},
    {"name": "Amazon (seyahat ekipmanı)", "url": "", "note": "valiz/kamera/adaptör"},
]


async def generate_travel_script(ask_llm, destination: str, lang: str = "en",
                                 highlights: int = 5) -> Dict:
    """Destinasyon → hook + öne çıkan noktalar + anlatım + her nokta için stok arama terimi."""
    prompt = (
        f"Create a punchy {lang} script for a 60-90s vertical travel short about: {destination}.\n"
        f"Structure: a 1-line HOOK (stop the scroll), then {highlights} must-see highlights. "
        f"Each highlight: one vivid spoken sentence + a specific stock-footage search phrase "
        f"(include the place name so real footage matches). Keep total ~120-160 words (slow-ish).\n"
        f"Also give a catchy youtube_title and a short thumbnail_hook (<=4 words).\n"
        f'ONLY JSON: {{"hook":"","title":"","thumbnail_hook":"","narration":"full spoken text",'
        f'"highlights":[{{"say":"","stock_query":""}}],"stock_keywords":["destination-based search phrases"]}}'
    )
    resp = await ask_llm(prompt=prompt, system_prompt="You are a viral travel content writer. Vivid, concise, specific. Output ONLY valid JSON.")
    try:
        m = re.search(r"```(?:json)?\s*(.*?)```", resp, re.DOTALL)
        s = m.group(1) if m else resp
        b = re.search(r"\{.*\}", s, re.DOTALL)
        d = json.loads(b.group(0) if b else s)
    except Exception:
        d = {}
    # güvenli varsayılanlar (LLM düşükse bile üretim dursun istemeyiz)
    d.setdefault("hook", f"{destination}: the trip you can't miss")
    d.setdefault("title", f"{destination} — Top Places You Must See")
    d.setdefault("thumbnail_hook", destination.split(",")[0][:20])
    d.setdefault("narration", d.get("hook", ""))
    d.setdefault("highlights", [])
    # stok anahtarları: destinasyon + highlight sorguları (birebir eşleşme)
    base = destination.split(",")[0]
    kws = d.get("stock_keywords") or []
    for h in d.get("highlights", []):
        q = h.get("stock_query")
        if q:
            kws.append(q)
    if not kws:
        kws = [f"{base} aerial", f"{base} street", f"{base} landmark", f"{base} nature", f"{base} sunset"]
    d["stock_keywords"] = kws[:8]
    return d
