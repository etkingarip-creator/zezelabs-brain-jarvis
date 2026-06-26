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


def break_even(fixed_monthly: float, net_contribution_per_customer: float) -> Dict:
    """Başa-baş müşteri sayısı: sabit maliyet / müşteri başı net katkı."""
    if net_contribution_per_customer <= 0:
        return {"reachable": False, "note": "müşteri başı net katkı ≤ 0 → başa-baş imkansız"}
    n = fixed_monthly / net_contribution_per_customer
    return {"reachable": True, "break_even_customers": int(n) + 1,
            "note": f"{int(n)+1} ödeyen müşteride başa-baş"}
