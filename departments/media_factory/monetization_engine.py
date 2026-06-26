"""
Monetization Engine — affiliate/açıklama-öncelikli gelir (faceless içerik stratejisi).

Kullanıcı stratejisi (doğrulandı: affiliate faceless'ta AdSense'in 2-4 katı):
ASIL kazanç açıklamadan gelir, AdSense değil (yavaş öder). Katmanlar:
1. Açıklama: videodaki araçların affiliate linkleri (tracked kısa URL) — EN ÜSTTE
2. Kendi kurulum rehberi (tutorial funnel — kişiliksiz güven)
3. Sabit yorum: teklif en üste sabit + tekrar
4. AdSense EN SONA eklenir
Hedef: patlama değil İSTİKRARLI TIRMANIŞ.

Saf/deterministik fonksiyonlar. Gelir projeksiyonu DÜRÜST (garanti değil, varsayım-açık).
"""
from __future__ import annotations
from typing import Dict, List


def _short_url(brand: str, tool: str) -> str:
    """Tracked temiz kısa URL (uzun affiliate URL'i daha az tık alır + iz tutmaz)."""
    slug = "".join(c for c in tool.lower() if c.isalnum())[:20]
    return f"bit.ly/{brand}-{slug}"


def build_description(topic: str, affiliate_tools: List[Dict], setup_guide_url: str = "",
                     brand: str = "zezelabs") -> str:
    """Affiliate-ÖNCELİKLİ açıklama. Araç linkleri en üstte (high-intent), sonra rehber,
    sonra ikincil CTA, AdSense notu EN SONDA. affiliate_tools: [{name, url, commission}]."""
    lines = [f"🎯 {topic} — videoda gösterdiğim TÜM araçlar (kurulum rehberiyle):", ""]
    # 1. AFFILIATE LİNKLER (en üst — asıl gelir)
    for t in affiliate_tools:
        nm = t.get("name", "araç")
        url = t.get("url") or _short_url(brand, nm)
        lines.append(f"👉 {nm}: {url}")
    lines.append("")
    # 2. KENDİ KURULUM REHBERİ (tutorial funnel)
    if setup_guide_url:
        lines.append(f"📘 Adım adım kurulum rehberim (ücretsiz): {setup_guide_url}")
        lines.append("")
    # 3. İkincil CTA
    lines.append("🔔 Bu tür araç incelemeleri için abone ol + bildirimleri aç.")
    lines.append("💬 Hangi aracı denedin? Yorumda yaz, yardımcı olayım.")
    lines.append("")
    # 4. AdSense / şeffaflık EN SONDA
    lines.append("—" * 3)
    lines.append("ℹ️ Bazı linkler affiliate linkidir (sana ek maliyet yok, kanala destek olur).")
    return "\n".join(lines)


def build_pinned_comment(primary_offer: str, primary_url: str, brand: str = "zezelabs") -> str:
    """Sabit yorum: teklifi en üste sabitle + tekrar et (en yüksek görünürlük noktası)."""
    url = primary_url or _short_url(brand, primary_offer)
    return (f"📌 EN ÇOK SORULAN: '{primary_offer}' → {url}\n"
            f"Kurulumda takılırsan buraya yaz, adım adım yardım ederim 👇 "
            f"(rehber + tüm linkler açıklamada)")


def monetization_stack(topic: str, affiliate_tools: List[Dict], setup_guide_url: str = "") -> Dict:
    """Tam katmanlı monetizasyon paketi — açıklama + sabit yorum + sıra (AdSense en son)."""
    primary = affiliate_tools[0] if affiliate_tools else {"name": "ana araç", "url": ""}
    return {
        "description": build_description(topic, affiliate_tools, setup_guide_url),
        "pinned_comment": build_pinned_comment(primary.get("name", "ana araç"), primary.get("url", "")),
        "layer_order": ["affiliate_links", "setup_guide", "secondary_cta", "adsense_last"],
        "primary_revenue": "affiliate (açıklama)", "secondary_revenue": "adsense (en son, yavaş)",
        "strategy": "İstikrarlı tırmanış: hafta1 indeks → hafta2 ilk affiliate → büyüyen izlenme",
    }


def revenue_projection(weekly_views: List[int], view_to_sale_pct: float = 0.3,
                       avg_commission_usd: float = 120.0, recurring: bool = False) -> Dict:
    """DÜRÜST gelir projeksiyonu (garanti DEĞİL — varsayımlar açık).
    view_to_sale: izlenme→satış oranı (0.5-3% CTR × 1-5% dönüşüm ≈ %0.1-0.5 tipik).
    avg_commission: satış başı (recurring programlar $120-200, 12 ay tekrar eder)."""
    weeks = []
    cumulative = 0.0
    active_recurring = 0.0
    for i, views in enumerate(weekly_views):
        sales = views * (view_to_sale_pct / 100.0)
        one_time = sales * avg_commission_usd
        if recurring:
            active_recurring += one_time  # her hafta taban büyür (12 ay tekrar)
            week_rev = active_recurring
        else:
            week_rev = one_time
        cumulative += week_rev
        weeks.append({"week": i + 1, "views": views, "sales": round(sales, 1),
                      "revenue_usd": round(week_rev, 2)})
    return {
        "weeks": weeks,
        "total_usd": round(cumulative, 2),
        "assumptions": f"izlenme→satış %{view_to_sale_pct}, satış başı ${avg_commission_usd}"
                       f"{' (recurring)' if recurring else ''}",
        "disclaimer": "Projeksiyon — garanti değil. Gerçek sonuç niş/CTR/dönüşüme bağlı; "
                      "istikrarlı tırmanış hedefle, tek video patlamasına güvenme.",
    }
