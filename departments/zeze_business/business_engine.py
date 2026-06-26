"""
Business Engine — zeze_business için hesaplanabilir iş matematiği (unicorn-seviye).

Muğlak LLM paragrafı değil; saf, deterministik, test edilebilir fonksiyonlar.
Unit economics + AI COGS (Replit dersi) + bottom-up market sizing + monetizasyon seçici.
"""
from __future__ import annotations
from typing import Dict, List


def unit_economics(price_monthly: float, gross_margin_pct: float, cac: float,
                   churn_monthly_pct: float, ai_cogs_monthly: float = 0.0) -> Dict:
    """Unit economics + AI COGS farkındalığı (Replit dersi: compute maliyeti marjı yer).
    LTV = (aylık brüt kâr - AI COGS) / churn. payback = CAC / aylık net katkı.
    Sağlıklı: LTV/CAC >= 3, payback <= 12 ay."""
    if churn_monthly_pct <= 0 or price_monthly <= 0:
        return {"valid": False, "reason": "geçersiz fiyat/churn"}
    gross_profit = price_monthly * (gross_margin_pct / 100.0)
    net_contribution = gross_profit - ai_cogs_monthly  # AI inference maliyeti düşülür
    lifetime_months = 100.0 / churn_monthly_pct
    ltv = net_contribution * lifetime_months
    ltv_cac = (ltv / cac) if cac > 0 else 0.0
    payback = (cac / net_contribution) if net_contribution > 0 else float("inf")
    margin_after_ai = (net_contribution / price_monthly * 100.0) if price_monthly else 0.0
    healthy = ltv_cac >= 3.0 and payback <= 12 and net_contribution > 0
    warnings = []
    if net_contribution <= 0:
        warnings.append("NET KATKI NEGATİF — AI COGS fiyatı aşıyor (Replit tuzağı)")
    if ltv_cac < 3:
        warnings.append(f"LTV/CAC {ltv_cac:.1f} < 3 (sürdürülemez edinim)")
    if payback > 12:
        warnings.append(f"Payback {payback:.1f} ay > 12 (nakit yakar)")
    return {
        "valid": True, "healthy": healthy,
        "ltv": round(ltv, 2), "cac": round(cac, 2), "ltv_cac_ratio": round(ltv_cac, 2),
        "payback_months": round(payback, 1) if payback != float("inf") else None,
        "net_contribution_monthly": round(net_contribution, 2),
        "margin_after_ai_pct": round(margin_after_ai, 1),
        "warnings": warnings,
    }


def bottom_up_som(target_users: int, conversion_pct: float, price_monthly: float,
                  capture_pct: float = 100.0) -> Dict:
    """Bottom-up SOM — top-down halüsinasyon değil, somut varsayımdan hesap.
    paying = hedef × dönüşüm × yakalama. ARR = paying × fiyat × 12."""
    paying = target_users * (conversion_pct / 100.0) * (capture_pct / 100.0)
    arr = paying * price_monthly * 12
    return {
        "reachable_users": int(target_users * capture_pct / 100.0),
        "paying_customers": int(paying),
        "som_arr_usd": round(arr, 0),
        "assumptions": f"{target_users} hedef × %{conversion_pct} dönüşüm × %{capture_pct} yakalama × ${price_monthly}/ay",
    }


def reconcile_market(top_down_tam: float, bottom_up_som_arr: float) -> Dict:
    """Top-down TAM ile bottom-up SOM tutarlı mı? SOM, TAM'ın makul bir oranı olmalı (<%10)."""
    if top_down_tam <= 0:
        return {"consistent": False, "note": "TAM yok"}
    ratio = bottom_up_som_arr / top_down_tam
    if ratio > 0.10:
        return {"consistent": False, "som_of_tam_pct": round(ratio * 100, 2),
                "note": f"SOM, TAM'ın %{ratio*100:.1f}'i — gerçekçi değil (>%10), varsayımları gözden geçir"}
    return {"consistent": True, "som_of_tam_pct": round(ratio * 100, 3),
            "note": "Bottom-up SOM top-down TAM ile tutarlı"}


def select_monetization(ai_cogs_per_use: float, usage_predictability: str = "değişken",
                        target: str = "b2c") -> Dict:
    """Somut monetizasyon modeli seç (5 model + outcome-based). AI COGS yüksek + değişken
    kullanımda flat-rate marjı öldürür → compute/usage-based güvenli."""
    if ai_cogs_per_use > 0.5 and usage_predictability == "değişken":
        model = "compute/usage-based ($/kullanım)"
        why = "Yüksek+değişken AI COGS → flat-rate marjı riskli (Replit tuzağı); kullanıma endeksle."
    elif target == "b2b":
        model = "hybrid (taban abonelik + kullanım üstü)"
        why = "B2B tahmin edilebilir taban gelir + kullanım üst sınırını korur."
    elif usage_predictability == "öngörülebilir":
        model = "flat-rate abonelik"
        why = "Öngörülebilir kullanım → basit flat-rate; tahsilat kolay."
    else:
        model = "prepaid kredi (outcome-based)"
        why = "Değişken kullanım + COGS koruması; $/tamamlanan-iş (2026 kayması)."
    return {"recommended_model": model, "rationale": why,
            "alternatives": ["flat-rate", "compute-based", "dimensional", "prepaid-credits", "hybrid"]}


# ──────────────────────────────────────────────────────────────────────────
# UNICORN'U AŞMA: duyarlılık + grounded benchmark + güven + otonom karar (H1-H4)
# ──────────────────────────────────────────────────────────────────────────

# H2 — sektör benchmark bantları (gerçek piyasa aralıkları; girdileri GIGO'dan kurtarır)
BENCHMARKS = {
    "saas_b2b":  {"cac": (300, 1200), "churn_monthly_pct": (1, 3),  "gross_margin_pct": (75, 85), "conversion_pct": (1, 4)},
    "saas_b2c":  {"cac": (20, 120),   "churn_monthly_pct": (3, 8),  "gross_margin_pct": (70, 85), "conversion_pct": (1, 3)},
    "ai_app":    {"cac": (30, 200),   "churn_monthly_pct": (4, 10), "gross_margin_pct": (50, 75), "conversion_pct": (1, 3)},
    "marketplace": {"cac": (10, 80),  "churn_monthly_pct": (3, 7),  "gross_margin_pct": (40, 65), "conversion_pct": (1, 5)},
}
NEW_ENTRANT_CAPTURE_PCT = (1.0, 5.0)  # yeni giren SAM'in %1-5'ini yakalar (frontier kuralı)


def extract_web_signals(text: str) -> Dict:
    """I2 — statik benchmark yerine GERÇEK web verisinden sayı çıkar (ücretsiz, canlı-ish).
    Büyüme %CAGR, pazar büyüklüğü $B/$M, fiyat $X/ay → bulunanlar 'web-grounded' işaretlenir."""
    import re as _re
    sig = {}
    # büyüme oranı (CAGR / growth)
    g = _re.search(r"(\d{1,2}(?:\.\d)?)\s*%\s*(?:cagr|growth|annual)", text, _re.IGNORECASE)
    if g:
        sig["growth_rate_pct"] = float(g.group(1))
    # pazar büyüklüğü → TAM
    mk = _re.search(r"\$\s*(\d+(?:\.\d+)?)\s*(billion|trillion|million|b|t|m)\b", text, _re.IGNORECASE)
    if mk:
        mult = {"billion": 1e9, "b": 1e9, "trillion": 1e12, "t": 1e12, "million": 1e6, "m": 1e6}[mk.group(2).lower()]
        sig["top_down_tam_usd"] = float(mk.group(1)) * mult
    # aylık fiyat
    pr = _re.search(r"\$\s*(\d+(?:\.\d+)?)\s*(?:/|per\s*)\s*mo", text, _re.IGNORECASE)
    if pr:
        sig["price_monthly"] = float(pr.group(1))
    return sig


def get_benchmark(industry: str = "ai_app") -> Dict:
    """Sektör benchmark bandı + orta nokta varsayılanları (tahmin yerine veri-temelli girdi)."""
    bands = BENCHMARKS.get(industry, BENCHMARKS["ai_app"])
    mid = {k: round((lo + hi) / 2, 2) for k, (lo, hi) in bands.items()}
    return {"industry": industry, "bands": bands, "midpoints": mid,
            "capture_pct_band": NEW_ENTRANT_CAPTURE_PCT}


def label_confidence(llm_keys: List[str], benchmark_keys: List[str] = None) -> Dict:
    """H3 — 3-katmanlı güven: gerçek-veri (LLM/web) / benchmark / tahmin. Şeffaflık = güven.
    Ağırlık: gerçek-veri 1.0, benchmark 0.5, tahmin 0."""
    benchmark_keys = set(benchmark_keys or [])
    llm_keys = set(llm_keys or [])
    keys = ["price_monthly", "cac", "churn_monthly_pct", "conversion_pct", "gross_margin_pct", "ai_cogs_monthly"]
    labels = {}
    score = 0.0
    for k in keys:
        if k in llm_keys:
            labels[k] = "gerçek-veri"; score += 1.0
        elif k in benchmark_keys:
            labels[k] = "benchmark"; score += 0.5
        else:
            labels[k] = "tahmin"
    confidence = round(score / len(keys) * 100)
    level = "yüksek" if confidence >= 67 else ("orta" if confidence >= 34 else "DÜŞÜK")
    return {"labels": labels, "confidence_pct": confidence, "level": level,
            "warning": "Girdiler çoğunlukla benchmark/tahmin — temkinli yaklaş" if confidence < 50 else ""}


def sensitivity(price_monthly: float, gross_margin_pct: float, cac: float,
                churn_monthly_pct: float, ai_cogs_monthly: float = 0.0) -> Dict:
    """H1 — tek sayı değil ARALIK + duyarlılık. Sürücüleri ±%40 oynatıp LTV/CAC'a etkisini ölç
    (tornado). En kötü senaryo da raporlanır (kırılganlık görünür)."""
    base = unit_economics(price_monthly, gross_margin_pct, cac, churn_monthly_pct, ai_cogs_monthly)
    base_ratio = base.get("ltv_cac_ratio", 0) if base.get("valid") else 0

    def ratio(cac_m=1.0, churn_m=1.0, price_m=1.0, cogs_m=1.0):
        u = unit_economics(price_monthly * price_m, gross_margin_pct, cac * cac_m,
                           churn_monthly_pct * churn_m, ai_cogs_monthly * cogs_m)
        return u.get("ltv_cac_ratio", 0) if u.get("valid") else 0

    drivers = {
        "CAC +%40": ratio(cac_m=1.4), "churn +%40": ratio(churn_m=1.4),
        "fiyat -%40": ratio(price_m=0.6), "AI COGS +%40": ratio(cogs_m=1.4),
    }
    # en duyarlı sürücü = base'den en çok uzaklaştıran
    tornado = sorted(drivers.items(), key=lambda kv: abs(kv[1] - base_ratio), reverse=True)
    worst = min([base_ratio] + list(drivers.values()))
    best = ratio(cac_m=0.7, churn_m=0.7)  # iyi senaryo
    return {
        "base_ltv_cac": base_ratio,
        "best_case_ltv_cac": round(best, 2),
        "worst_case_ltv_cac": round(worst, 2),
        "most_sensitive_driver": tornado[0][0] if tornado else None,
        "tornado": {k: round(v, 2) for k, v in drivers.items()},
        "robust": worst >= 3.0,  # en kötü senaryoda bile sağlıklı mı (dayanıklılık)
    }


def go_no_go(unit_econ: Dict, sens: Dict = None) -> Dict:
    """H4 — OTONOM KARAR (rapor değil): holding bu app'i yapmalı mı? Kötü unit economics → NO-GO.
    app_factory bu karara göre build eder/etmez. Rakipler 'analiz' verir; biz KARAR veririz."""
    if not unit_econ.get("valid"):
        return {"decision": "NO-GO", "reasons": ["geçersiz unit economics (girdi yetersiz)"]}
    reasons = []
    if unit_econ.get("net_contribution_monthly", 0) <= 0:
        reasons.append("Net katkı ≤ 0 (AI COGS fiyatı aşıyor — her müşteri zarar)")
    if unit_econ.get("ltv_cac_ratio", 0) < 3:
        reasons.append(f"LTV/CAC {unit_econ.get('ltv_cac_ratio')} < 3 (sürdürülemez)")
    pb = unit_econ.get("payback_months")
    if pb is None or pb > 18:
        reasons.append(f"Payback {pb} ay > 18 (nakit yakar)")
    if sens and not sens.get("robust", True):
        reasons.append(f"En kötü senaryoda LTV/CAC {sens.get('worst_case_ltv_cac')} < 3 (kırılgan)")
    decision = "GO" if not reasons else "NO-GO"
    return {"decision": decision, "reasons": reasons or ["unit economics sağlıklı + dayanıklı"]}


def break_even(fixed_monthly: float, net_contribution_per_customer: float) -> Dict:
    """Başa-baş müşteri sayısı: sabit maliyet / müşteri başı net katkı."""
    if net_contribution_per_customer <= 0:
        return {"reachable": False, "note": "müşteri başı net katkı ≤ 0 → başa-baş imkansız"}
    n = fixed_monthly / net_contribution_per_customer
    return {"reachable": True, "break_even_customers": int(n) + 1,
            "note": f"{int(n)+1} ödeyen müşteride başa-baş"}
