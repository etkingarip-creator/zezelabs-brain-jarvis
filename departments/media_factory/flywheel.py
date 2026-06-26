"""
Self-Improving Flywheel — media_factory'yi generator'dan ÖĞRENEN sisteme çevirir.

Frontier farkı: unicorn içerik makinesi HER HAFTA daha iyi olur (statik generator değil).
Döngü: üret → yayınla → GERÇEK performans → KAZANAN paterni öğren → sonraki üretimi yanlıla.

Saf/deterministik fonksiyonlar + JSON defter. Performans GERÇEK olduğunda (YouTube API)
beslenir; yoksa skor-tabanlı proxy ile başlar, gerçek veri geldikçe keskinleşir.
"""
from __future__ import annotations
import json
import os
from typing import Dict, List
from collections import defaultdict


def record_performance(ledger_path: str, entry: Dict) -> None:
    """O1 — bir videonun özelliklerini + performansını deftere ekle.
    entry: {niche, title_features:[...], hook_type, title_ctr, thumb_ctr, retention_pct, conversion_pct}"""
    os.makedirs(os.path.dirname(ledger_path), exist_ok=True)
    ledger = load_ledger(ledger_path)
    ledger.append(entry)
    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(ledger[-500:], f, ensure_ascii=False, indent=2)


def load_ledger(ledger_path: str) -> List[Dict]:
    if not os.path.exists(ledger_path):
        return []
    try:
        with open(ledger_path, encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def _perf(entry: Dict) -> float:
    """Birleşik performans skoru: gerçek CTR/retention varsa onlar, yoksa üretim skoru proxy."""
    # gerçek metrikler (varsa) ağırlıklı; yoksa title/thumb skoru proxy
    real = entry.get("retention_pct", 0) * 0.5 + entry.get("conversion_pct", 0) * 10
    proxy = (entry.get("title_ctr", 0) + entry.get("thumb_ctr", 0)) / 2
    return real if real > 0 else proxy


def learn_winning_patterns(ledger: List[Dict], min_samples: int = 3) -> Dict:
    """O2 — defterden KAZANAN paternleri çıkar. Hangi niş / başlık-özelliği / hook en yüksek
    performans aldı (yeterli örneklem varsa). Veri-güdümlü, varsayım değil."""
    if len(ledger) < min_samples:
        return {"ready": False, "note": f"Yetersiz veri ({len(ledger)}/{min_samples}) — öğrenme için biriktir"}
    dims = {"niche": defaultdict(list), "hook_type": defaultdict(list), "title_feature": defaultdict(list)}
    for e in ledger:
        p = _perf(e)
        if e.get("niche"):
            dims["niche"][e["niche"]].append(p)
        if e.get("hook_type"):
            dims["hook_type"][e["hook_type"]].append(p)
        for tf in e.get("title_features", []):
            dims["title_feature"][tf].append(p)
    winners = {}
    for dim, groups in dims.items():
        ranked = sorted(((k, sum(v) / len(v), len(v)) for k, v in groups.items() if v),
                        key=lambda x: x[1], reverse=True)
        winners[dim] = [{"value": k, "avg_perf": round(a, 1), "samples": n} for k, a, n in ranked[:3]]
    return {"ready": True, "winners": winners, "total_videos": len(ledger)}


def winning_brief(patterns: Dict) -> str:
    """O3 — kazanan paternleri sonraki ÜRETİME enjekte edilecek metne çevir (flywheel)."""
    if not patterns.get("ready"):
        return ""
    w = patterns["winners"]
    lines = ["[KENDİ VERİNDEN KAZANAN PATERNLER — bunları tekrarla]"]
    if w.get("niche"):
        lines.append("En iyi nişler: " + ", ".join(f"{x['value']} (perf {x['avg_perf']})" for x in w["niche"]))
    if w.get("hook_type"):
        lines.append("En iyi hook'lar: " + ", ".join(f"{x['value']}" for x in w["hook_type"]))
    if w.get("title_feature"):
        lines.append("En iyi başlık özellikleri: " + ", ".join(f"{x['value']}" for x in w["title_feature"]))
    return "\n".join(lines)


def flywheel_improvement(ledger: List[Dict], window: int = 5) -> Dict:
    """O4 — flywheel çalışıyor mu? İlk N video vs son N video ortalama performansı.
    İyileşme >0 ise makine kendi verisinden öğreniyor demektir."""
    if len(ledger) < window * 2:
        return {"measurable": False, "note": f"Ölçüm için {window*2}+ video gerekli ({len(ledger)} var)"}
    early = [_perf(e) for e in ledger[:window]]
    recent = [_perf(e) for e in ledger[-window:]]
    e_avg, r_avg = sum(early) / window, sum(recent) / window
    delta = r_avg - e_avg
    return {"measurable": True, "early_avg": round(e_avg, 1), "recent_avg": round(r_avg, 1),
            "improvement": round(delta, 1), "improving": delta > 0,
            "note": "Flywheel çalışıyor — son videolar daha iyi" if delta > 0
                    else "İyileşme yok — paternler/üretim gözden geçirilmeli"}


def classify_title_features(title: str) -> List[str]:
    """Başlığı özellik etiketlerine ayır (öğrenme boyutu)."""
    import re
    low = (title or "").lower()
    feats = []
    if re.search(r"\d", title or ""):
        feats.append("sayı_var")
    if any(w in low for w in ["sır", "kimse", "yanlış", "neden", "aslında", "gerçek"]):
        feats.append("merak")
    if any(w in low for w in ["bedava", "ücretsiz", "$", "dolar", "kazan"]):
        feats.append("para/bedava")
    if any(w in low for w in ["2026", "yeni", "şimdi"]):
        feats.append("güncellik")
    if "?" in (title or ""):
        feats.append("soru")
    return feats or ["nötr"]
