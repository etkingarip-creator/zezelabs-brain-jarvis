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
    """Destinasyon → hook + 4 KATEGORİ (görülecek yerler/enteresan bilgi/ulaşım/konaklama) +
    170-210 kelime (60-88sn) + her kategori için stok arama terimi + affiliate köprüsü."""
    prompt = (
        f"Write a punchy {lang} script for a 60-88 SECOND vertical travel short about: {destination}.\n"
        f"TOTAL 170-210 words (this controls the 60-88s length — stay in range).\n"
        f"Structure EXACTLY: 1-line HOOK, then 4 categories, each 2-3 vivid spoken sentences:\n"
        f"1) MUST-SEE spots (top places), 2) INTERESTING facts (surprising), "
        f"3) GETTING THERE / getting around (transport), 4) WHERE TO STAY (accommodation), then a 1-line CTA.\n"
        f"Each category: also give a stock-footage search phrase INCLUDING the place name (real footage match).\n"
        f"Also: catchy youtube_title, short thumbnail_hook (<=3 words).\n"
        f'ONLY JSON: {{"hook":"","title":"","thumbnail_hook":"","narration":"full spoken text 170-210 words",'
        f'"categories":[{{"name":"must_see|facts|transport|stay","say":"","stock_query":""}}],'
        f'"stock_keywords":["destination-based phrases per category"]}}'
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
    d.setdefault("categories", d.get("highlights", []))
    # stok anahtarları: destinasyon + kategori sorguları (birebir eşleşme)
    base = destination.split(",")[0]
    kws = d.get("stock_keywords") or []
    for h in d.get("categories", []):
        q = h.get("stock_query")
        if q:
            kws.append(q)
    if not kws:  # 4 kategoriye uygun varsayılan aramalar
        kws = [f"{base} landmark", f"{base} aerial city", f"{base} street food",
               f"{base} transport road", f"{base} hotel resort", f"{base} sunset nature"]
    d["stock_keywords"] = kws[:8]
    return d
