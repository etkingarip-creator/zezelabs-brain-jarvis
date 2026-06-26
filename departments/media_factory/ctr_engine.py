"""
CTR Engine — asıl kaldıraç: thumbnail + title + niş (faceless başarının >%50'si).

Araştırma (2026): thumbnail başarının yarısından fazlası; CTR<%3 → algoritma rafa kaldırır;
niş seçimi araç yığınından önemli. Bu motor script'i DEĞİL, asıl kaldıraçları ölçer.
Saf, deterministik, test edilebilir.
"""
from __future__ import annotations
import re
from typing import Dict, List

# Yüksek-CTR title sinyalleri
_CURIOSITY = ["sır", "kimse", "aslında", "bilmediğin", "yanlış", "neden", "nasıl", "gerçek",
              "asla", "şok", "meğer", "sandığın", "gizli", "kanıt"]
_POWER = ["bedava", "ücretsiz", "saniyede", "dakikada", "kolay", "hızlı", "yeni", "2026",
          "dolar", "$", "kazan", "patladı", "çöktü", "vs", "en iyi", "test ettim"]
_NUMBER = r"\b\d+\b"
_EXTREME = ["herkes", "kimse", "hiç", "tek", "sadece", "asla", "her zaman"]


def score_title(title: str) -> Dict:
    """Title CTR potansiyeli 0-100 + düzeltme. Faceless: merak + sayı + güç-kelime + netlik."""
    t = (title or "").strip()
    if not t:
        return {"score": 0, "fixes": ["boş başlık"]}
    low = t.lower()
    score = 0.0
    fixes = []
    # merak boşluğu (30)
    if any(w in low for w in _CURIOSITY):
        score += 30
    else:
        fixes.append("Merak boşluğu ekle (sır/neden/yanlış/kimse...)")
    # sayı/liste (15)
    if re.search(_NUMBER, t):
        score += 15
    else:
        fixes.append("Sayı ekle (3 yol, 7 hata...) — net vaat")
    # güç kelime (20)
    if any(w in low for w in _POWER):
        score += 20
    else:
        fixes.append("Güç kelime ekle (bedava/saniyede/$/2026)")
    # aşırılık/kontrast (15)
    if any(w in low for w in _EXTREME):
        score += 15
    # netlik/uzunluk (~40-65 karakter ideal) (20)
    n = len(t)
    if 30 <= n <= 65:
        score += 20
    elif n > 70:
        fixes.append(f"Çok uzun ({n} karakter) — 65 altına indir (mobilde kesilir)")
    else:
        fixes.append(f"Çok kısa ({n}) — netleştir/somutlaştır")
    score = round(min(100, score))
    return {"score": score, "ctr_ready": score >= 60, "length": n, "fixes": fixes}


def score_thumbnail_concept(concept: str) -> Dict:
    """Thumbnail KONSEPT'ini CTR ilkelerine göre skorla (üretilen tarif). Yüksek kontrast,
    tek odak, büyük okunur metin (3-4 kelime), duygu/obje, renk patlaması."""
    c = (concept or "").lower()
    score = 0.0
    fixes = []
    rules = {
        "yüksek kontrast / canlı renk": ["kontrast", "canlı", "parlak", "renk", "sarı", "kırmızı", "neon"],
        "tek net odak noktası": ["tek", "odak", "merkez", "büyük", "yakın", "obje"],
        "büyük okunur metin (3-4 kelime)": ["metin", "yazı", "kelime", "büyük font", "kalın"],
        "duygu/merak tetikleyici": ["şaşkın", "şok", "ok işareti", "kırmızı daire", "duygu", "merak"],
    }
    for label, kws in rules.items():
        if any(k in c for k in kws):
            score += 25
        else:
            fixes.append(f"Eksik: {label}")
    score = round(min(100, score))
    return {"score": score, "ctr_ready": score >= 75, "fixes": fixes}


def score_niche(demand: float, cpm_tier: str, competition: float,
                monetizable: bool = True) -> Dict:
    """N2 — niş skoru: 'araç yığınından önemli'. demand/competition 0-100, cpm_tier low/mid/high.
    Yüksek CPM nişler (finans/tech/AI) + yüksek talep + düşük rekabet = kazanan."""
    cpm_score = {"high": 40, "mid": 25, "low": 10}.get(cpm_tier, 15)
    score = demand * 0.35 + cpm_score - competition * 0.25 + (10 if monetizable else 0)
    score = round(max(0, min(100, score)))
    verdict = "güçlü niş" if score >= 60 else "orta" if score >= 40 else "zayıf (kaçın)"
    notes = []
    if cpm_tier == "low":
        notes.append("Düşük CPM — affiliate/ürün gerekir, AdSense yetmez")
    if competition >= 70:
        notes.append("Yüksek rekabet — alt-niş veya açı farklılaştır")
    if demand < 40:
        notes.append("Düşük talep — büyüme yavaş")
    return {"score": score, "verdict": verdict, "notes": notes or ["dengeli niş"]}


def channel_consistency(videos: List[Dict]) -> Dict:
    """N3 — YouTube 2026 kanalı BÜTÜN yargılar. Niş/format tutarlılığı + kadans (haftada-1).
    videos: [{niche, format}]. Dağınık niş → algoritma kafası karışır."""
    if not videos:
        return {"consistent": True, "note": "henüz video yok"}
    niches = [v.get("niche", "") for v in videos]
    formats = [v.get("format", "") for v in videos]
    niche_focus = (niches.count(max(set(niches), key=niches.count)) / len(niches)) if niches else 0
    fmt_focus = (formats.count(max(set(formats), key=formats.count)) / len(formats)) if formats else 0
    consistent = niche_focus >= 0.7 and fmt_focus >= 0.6
    return {"consistent": consistent, "niche_focus_pct": round(niche_focus * 100),
            "format_focus_pct": round(fmt_focus * 100),
            "note": "Tutarlı kanal (algoritma net konumlar)" if consistent
                    else "Dağınık — tek niş/formata odaklan (algoritma kanalı bütün yargılar)"}
