"""
Niche Blueprint — AI araçları/tech kanalı için sabit içerik şablonu (kanal tutarlılığı).

'İçerik yetersiz' sorununun kökü: jenerik laflar. Çözüm: SPESİFİK + GÖSTEREN yapı.
Her video aynı yüksek-standart iskeleti izler → kanal tutarlı, algoritma net konumlar.
"""
from typing import Dict, List

NICHE = "ai_tools"

# SENARYO ŞABLONU — 'yetersiz içerik' panzehiri: her segment SOMUT olmalı (araç adı, sayı, sonuç)
SCRIPT_TEMPLATE: List[Dict] = [
    {"role": "hook", "sec": "0-3", "kural": "Cesur somut iddia + merak. Belirsiz değil sayılı.",
     "ornek_en": "This FREE AI tool replaces a $2,000/month employee."},
    {"role": "problem", "sec": "3-9", "kural": "İzleyicinin SPESİFİK acısı (zaman/para kaybı).",
     "ornek_en": "You're wasting 10 hours a week doing this by hand."},
    {"role": "demo", "sec": "9-40", "kural": "ARACI GÖSTER: tam ad + 2-3 somut adım + GERÇEK çıktı. "
     "Asıl derinlik burada — jenerik 'çok faydalı' YASAK, ne yaptığını adım adım anlat.",
     "ornek_en": "Step 1: paste your topic. Step 2: pick a voice. 30 seconds later — a full video."},
    {"role": "proof", "sec": "40-45", "kural": "Somut sonuç/sayı/kıyas (öncesi-sonrası).",
     "ornek_en": "What took me 3 hours now takes 3 minutes."},
    {"role": "cta", "sec": "45-50", "kural": "Tek net eylem + affiliate yönlendir (sabit yorum/açıklama).",
     "ornek_en": "Free link in the pinned comment — try it before they add a paywall."},
]

# ALTYAZI SPEC — taşmasız, hiyerarşili (narrated_video build_ass ile uyumlu)
SUBTITLE_SPEC = {
    "font": "Arial", "body_size": 52, "hook_size": 64,
    "max_chars_per_line": 16, "max_lines": 2,
    "body_color": "beyaz", "hook_color": "sarı (vurgu)",
    "position": "alt-üçte-bir (MarginV ~360)", "outline": "kalın siyah + gölge",
    "keyword_highlight": "araç adı/sayı vurgulanmalı (büyük harf/sarı)",
    "timing": "segment-bazlı, seslendirmeyle senkron",
}

# EKRAN DÜZENİ & HİYERARŞİ — dikey 1080x1920 bölgeler (üstten alta öncelik)
LAYOUT_ZONES = {
    "top_bar (0-12%)": "Kanal handle (küçük) + opsiyonel ilerleme/bölüm etiketi",
    "hook_title (12-25%)": "İlk 3sn büyük HOOK metni (en üst hiyerarşi) — sonra kaybolur",
    "main_stage (25-72%)": "ANA GÖRSEL: araç demo / b-roll — odak noktası, en büyük alan",
    "subtitle_band (72-88%)": "TR altyazı (alt-üçte-bir, okunur)",
    "cta_bar (88-100%)": "Sabit CTA şeridi: 'Link sabit yorumda' + ok/parmak emoji",
}
HIERARCHY = ["1. Hook metni (ilk 3sn)", "2. Ana görsel (demo)", "3. Altyazı", "4. CTA şeridi"]


def build_script_prompt(topic: str) -> str:
    """LLM'e verilecek SOMUT senaryo prompt'u (jenerik içeriği engeller)."""
    tmpl = "\n".join(f"- {s['role'].upper()} ({s['sec']}sn): {s['kural']} Örn: \"{s['ornek_en']}\""
                     for s in SCRIPT_TEMPLATE)
    return (
        f"KONU (AI araçları/tech): {topic}\n\n"
        f"Bu SABİT yapıyı izle (her segment SOMUT olmalı — araç adı, sayı, gerçek adım; "
        f"jenerik 'çok faydalı/harika' YASAK):\n{tmpl}\n\n"
        f"5-6 segment. Her segment İngilizce seslendirme(en) + kısa TR altyazı(tr, max 5 kelime). "
        f'SADECE JSON: {{"segments":[{{"en":"...","tr":"..."}}], "affiliate_tool":"araç"}}'
    )
