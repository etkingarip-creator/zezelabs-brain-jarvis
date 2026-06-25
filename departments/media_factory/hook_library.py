"""
Hook Library — kanıta dayalı viral kısa-video kanca taksonomisi.

118.584+ viral video analizine dayanan hook tipleri. media_factory bu kütüphaneyi
kullanarak generic içerik değil, viral mekanik bilen script üretir (domain-fitness).

Kaynaklar: OpusClip, CreatorsJet, vexub viral hook framework araştırmaları (2026).
"""
from typing import Dict, List

# Kanca tipleri: id -> {ad, mekanizma, örnek kalıp}
HOOKS: Dict[str, Dict[str, str]] = {
    # ── Merak temelli (curiosity gap / open loop) ──
    "curiosity_gap":   {"ad": "Merak Boşluğu", "mekanizma": "Tamamlanmamış bilgi → beyin kapatmak ister (açık döngü)",
                        "ornek": "Bunu öğrenince bir daha eskisi gibi yapamayacaksın..."},
    "question":        {"ad": "Soru Kancası", "mekanizma": "Hedef kitlenin cevabını çok istediği soru",
                        "ornek": "Neden herkes X yapıyor da sen hâlâ Y'desin?"},
    "list_tease":      {"ad": "Liste Tease", "mekanizma": "Sayılı vaat + merak",
                        "ornek": "Kimsenin söylemediği 3 şey..."},
    # ── Sarsıcı / kontrarian ──
    "contrarian":      {"ad": "Kontrarian İddia", "mekanizma": "Yaygın inancı sarsar",
                        "ornek": "Çoğu kişi bunu tamamen yanlış biliyor."},
    "mistake_warning": {"ad": "Hata Uyarısı", "mekanizma": "Kayıp korkusu (loss aversion)",
                        "ornek": "Y istiyorsan X yapmayı HEMEN bırak."},
    "myth_fact":       {"ad": "Mit vs Gerçek", "mekanizma": "Beklenti kırma + öğretici",
                        "ornek": "Sandığın gibi değil — gerçek şu:"},
    # ── Görsel / ritim (pattern interrupt) ──
    "visual_interrupt":{"ad": "Şok Görsel Kanca", "mekanizma": "Beklenmedik obje/hareket → kaydırma paterni kırılır",
                        "ornek": "Beklenmedik bir objeyi ani bir hareketle bırak (0-1sn)"},
    "before_after":    {"ad": "Önce/Sonra Snap", "mekanizma": "Ani dönüşüm kontrastı",
                        "ornek": "Bu haldeydi → 3 saniyede şuna döndü"},
    # ── Duygusal ──
    "pain_first":      {"ad": "Kişisel Problem Kancası", "mekanizma": "İzleyicinin acı noktasını aynalar → empati → izlenme",
                        "ornek": "Eğer sen de geceleri bunu düşünüyorsan..."},
    "micro_story":     {"ad": "Mikro Hikaye", "mekanizma": "Anında karaktere bağlanma",
                        "ornek": "Dün biri bana şunu dedi ve hayatım değişti:"},
    # ── Yanlış yönlendirme ──
    "misdirection":    {"ad": "Yanlış Yönlendirme", "mekanizma": "Beyni 'yaşanacak mı' beklentisine sokar → süre artar",
                        "ornek": "Bunu yapacağımı sandın ama..."},
    # ── Güven ──
    "proof_first":     {"ad": "Önce Kanıt", "mekanizma": "Sonucu önce göster → güven → dikkat yatırımı",
                        "ornek": "Bu sonucu 7 günde aldım, nasıl olduğunu göstereceğim:"},
    "authority":       {"ad": "Otorite Sinyali", "mekanizma": "İlk saniyede kredibilite",
                        "ornek": "10 yıldır bunu yapıyorum, tek kuralım şu:"},
    # ── Aciliyet ──
    "urgency":         {"ad": "Aciliyet Penceresi", "mekanizma": "Kaçırma korkusu (FOMO)",
                        "ornek": "Bunu bugün yapmazsan geç kalacaksın."},
}

# En çok kazanan 2026 kombinasyon formülü
WINNING_FORMULA = "Otorite Sinyali (1.sn) → Merak Boşluğu (2.sn) → Vaat (3.sn)"


def build_hook_brief(max_hooks: int = 4) -> str:
    """Script üretim prompt'una eklenecek hook rehberi metni."""
    lines = ["[VİRAL HOOK KÜTÜPHANESİ — kanıta dayalı, zorunlu kullan]"]
    lines.append(f"İlk 3 saniye dağıtımı belirler (3sn'yi geçenlerin %65'i 10sn+ izler).")
    lines.append("Katmanlı hook (görsel+işitsel+metin aynı anda) 3sn tutmayı 3× artırır.")
    lines.append("Pattern interrupt her 30-60sn tekrarlanmalı. İskelet: Hook→Problem→Çözüm→CTA.")
    lines.append(f"En güçlü kombinasyon: {WINNING_FORMULA}\n")
    lines.append("Kullanılabilir kancalar:")
    for hid, h in HOOKS.items():
        lines.append(f"- {h['ad']} ({hid}): {h['mekanizma']} | Örn: \"{h['ornek']}\"")
    lines.append("\nKURAL: Her script EN AZ 1 kanca tipini açıkça kullanmalı ve ilk 3 saniyeye yerleştirmeli.")
    return "\n".join(lines)


def list_hook_ids() -> List[str]:
    return list(HOOKS.keys())
