"""
Departman Routing — TEK DOĞRULUK KAYNAĞI (17 departman).

Sorun: routing 4 yere dağılmıştı, eksik/yanlış departman listeleriyle (zeze_media, zeze_eng...).
Çözüm: burası tek kaynak. Tüm routerlar (backend/jarvis _route_to_department, LLM router,
task_classifier) buradan beslenir. Skor-tabanlı: en çok/önemli keyword eşleşen departman kazanır.
"""
from __future__ import annotations
import re
from typing import Dict, List, Tuple

# Her departman: kısa açıklama (LLM router için) + keyword listesi (deterministik router için).
# Keyword'ler kapsamlı + niş-spesifik. Çakışmalar skorla çözülür (spesifik > jenerik).
DEPARTMENT_ROUTING: Dict[str, Dict] = {
    "media_factory": {
        "desc": "Video/short üretimi, seyahat & içerik kanalları, sosyal medya videoları, ses/altyazı/montaj.",
        "keywords": ["video", "short", "shorts", "reel", "reels", "tiktok", "youtube", "kanal",
                     "seyahat", "travel", "gezi", "destinasyon", "destination", "trip",
                     "içerik", "montaj", "altyazı", "thumbnail", "kapak", "seslendirme", "podcast",
                     "uyku hikaye", "sleep story", "mikrodrama", "klip", "animasyon", "ses", "görüntü",
                     "sevimli hayvan", "cute animal", "vlog", "belgesel"]},
    "zeze_design": {
        "desc": "Grafik/UI/UX tasarımı, logo, marka, mockup, arayüz — video DEĞİL.",
        "keywords": ["ui", "ux", "arayüz", "logo", "marka kimlik", "mockup", "figma", "tasarla",
                     "grafik tasarım", "wireframe", "renk paleti", "tipografi", "buton tasarım"]},
    "zeze_dev": {
        "desc": "Kod yazımı, yazılım mühendisliği, hata ayıklama, mimari, deploy.",
        "keywords": ["kod", "kod yaz", "yazılım", "geliştir", "program", "git", "commit", "bug",
                     "hata ayıkla", "refactor", "api geliştir", "backend", "frontend", "deploy",
                     "code", "develop", "debug", "function", "class", "algoritma"]},
    "app_factory": {
        "desc": "Full-stack uygulama + SaaS üretimi (DB+auth+deploy), MVP, web/mobil app.",
        "keywords": ["uygulama", "app yap", "saas", "web app", "mobil uygulama", "mvp", "startup ürün",
                     "fastapi", "web sitesi", "landing page", "abonelik ürün", "full-stack"]},
    "crypto_trading": {
        "desc": "Kripto alım-satım, portföy, risk, strateji (live trade kapalı).",
        "keywords": ["kripto", "crypto", "bitcoin", "btc", "ethereum", "bnb", "coin", "trade",
                     "trading", "binance", "cüzdan", "bakiye", "portföy", "kaldıraç", "spot"]},
    "zeze_betting": {
        "desc": "Bahis/oran analizi, kantitatif tahmin, value bet.",
        "keywords": ["bahis", "betting", "oran", "kupon", "tuttur", "iddaa", "value bet", "maç tahmin"]},
    "zeze_business": {
        "desc": "İş stratejisi, pazar analizi, iş modeli, roadmap, birim ekonomi.",
        "keywords": ["iş stratejisi", "iş modeli", "pazar analiz", "roadmap", "büyüme strateji",
                     "gelir modeli", "cac", "ltv", "go-to-market", "rakip analiz", "swot"]},
    "zeze_trend": {
        "desc": "Trend istihbaratı, yükselen konular, zayıf sinyal, pazar yönü.",
        "keywords": ["trend", "yükselen", "zayıf sinyal", "hype", "popüler ne", "gelecek trend",
                     "trend araştır", "viral konu"]},
    "zeze_aro": {
        "desc": "Analitik, büyüme, funnel, ROI, metrik, A/B test, elde tutma.",
        "keywords": ["analitik", "metrik", "funnel", "roi", "dönüşüm", "a/b test", "churn",
                     "kohort", "büyüme hack", "kpi", "elde tutma"]},
    "zeze_comms": {
        "desc": "İletişim/PR, duyuru, basın, e-posta, blog metni (video değil).",
        "keywords": ["iletişim", "duyuru", "basın", "pr", "press", "e-posta kampanya", "blog yazı",
                     "haber bülteni", "newsletter", "sosyal medya metin"]},
    "zeze_compliance": {
        "desc": "Hukuk/uyum, KVKK/GDPR, düzenleme, politika, sözleşme.",
        "keywords": ["uyum", "kvkk", "gdpr", "yasal", "hukuk", "sözleşme", "düzenleme", "politika",
                     "compliance", "legal", "gizlilik politika", "telif"]},
    "zeze_sec": {
        "desc": "Güvenlik, pentest, zafiyet tarama, tehdit modelleme, denetim.",
        "keywords": ["güvenlik", "pentest", "zafiyet", "sızma test", "tehdit", "audit", "owasp",
                     "security", "vulnerability", "şifreleme", "saldırı yüzeyi"]},
    "zeze_ops": {
        "desc": "Operasyon, süreç iyileştirme, otomasyon, SLA, kapasite.",
        "keywords": ["operasyon", "süreç iyileştir", "otomasyon", "sla", "kapasite", "darboğaz",
                     "verimlilik süreç", "runbook", "workflow otomasyon"]},
    "zeze_production": {
        "desc": "Fiziksel/proje üretim yönetimi, kalite kapıları, teslim planı (video DEĞİL).",
        "keywords": ["üretim planı", "kalite kapı", "teslim planı", "kritik yol", "tedarik",
                     "proje teslim", "wip limit"]},
    "zeze_rnd": {
        "desc": "Ar-Ge, teknoloji değerlendirme, prototip, yenilik, repo tarama.",
        "keywords": ["araştırma", "ar-ge", "r&d", "prototip", "teknoloji değerlendir", "yenilik",
                     "poc", "repo tara", "yeni araç dene", "deney tasarla"]},
    "zeze_academy": {
        "desc": "Eğitim/müfredat, öğrenme içeriği, kurs, ders tasarımı.",
        "keywords": ["eğitim", "müfredat", "kurs", "ders", "öğren", "öğretim", "curriculum",
                     "quiz", "öğrenme yolu"]},
    "zeze_game": {
        "desc": "Oyun tasarımı/geliştirme, çekirdek döngü, seviye, karakter.",
        "keywords": ["oyun", "game", "gaming", "level tasarım", "oyun mekanik", "karakter tasarım",
                     "core loop", "unity", "unreal", "godot"]},
}

# Jenerik/çok-anlamlı kelimeler tek başına düşük ağırlık (yanlış yönlendirmeyi azalt).
_GENERIC = {"video", "ses", "içerik", "analiz", "pazar", "test", "üretim", "media", "ai"}


def route(text: str, default: str = "zeze_business") -> Tuple[str, float, bool]:
    """Skor-tabanlı departman seçimi. Dönüş: (departman, skor, kesin_eşleşme)."""
    t = (text or "").lower()
    scores: Dict[str, float] = {}
    for dept, cfg in DEPARTMENT_ROUTING.items():
        s = 0.0
        for kw in cfg["keywords"]:
            if re.search(r"\b" + re.escape(kw.lower()), t):
                s += 0.4 if kw in _GENERIC else 1.0  # spesifik keyword > jenerik
        if s:
            scores[dept] = s
    if not scores:
        return default, 0.0, False
    best = max(scores, key=scores.get)
    return best, scores[best], scores[best] >= 1.0


def departments_brief() -> str:
    """LLM router için 17 departman + açıklama (tek kaynaktan)."""
    return "\n".join(f"- {d}: {c['desc']}" for d, c in DEPARTMENT_ROUTING.items())
