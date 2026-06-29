"""
Niş Araştırma Playbook — media_factory'nin TÜM AI çalışanlarının öğrenip uyacağı disiplin.

Kullanıcı vizyonu: "Profesyoneller nişi tahmin ederek seçmez. Önce talebi ölçer, sonra
rekabeti inceler, en son üretim sistemini kurar." (YouTube/TikTok/IG · dikey/yatay/uzun)

5 aşamalı huni (geliştirilmiş: gerçek-veri + sayısal eşik + platform/format eşlemesi):
  1. Talep ölç → karlı niş bul + 10 üzerinden puanla + en iyi 5
  2. Her nişi gir/girilmez kararına bağla (sayısal eşik)
  3. Seçilen niş için 10 düşük-rekabet alt-niş (platform/format dahil)
  4. Rakip analizi → uygulanabilir kanal başlangıç stratejisi
  5. 30 günlük test planı + net kill/continue eşikleri
"""

# Tüm AI çalışanlara enjekte edilecek ÇEKİRDEK DİSİPLİN
PLAYBOOK_DIRECTIVE = (
    "\n\n[NİŞ ARAŞTIRMA DİSİPLİNİ — ZORUNLU]\n"
    "Profesyonel sıra: 1) TALEBİ ÖLÇ (tahmin etme) → 2) REKABETİ İNCELE → 3) ÜRETİM SİSTEMİ KUR.\n"
    "Asla niş tahmin etme; gerçek sinyal (YT autocomplete/Reddit/Trends yönü) + sayısal kanıt iste.\n"
    "Her niş kararı 'gir/girilmez' net olmalı, sayısal eşiğe bağlı. Genel/muğlak cevap YASAK.\n"
    "Platform+format eşle (YouTube uzun/Shorts, TikTok/IG dikey). Gelir yolu ≥2 olmalı.\n"
    "Her plan net kill/continue eşiği içermeli (izlenme, CTR≥%4, retention, abone)."
)

# Sayısal eşikler (gir/girilmez ve kill/continue kararları)
THRESHOLDS = {
    "min_demand_score": 6,        # 10 üzerinden talep
    "max_competition_score": 6,   # 10 üzerinden (düşük iyi)
    "min_revenue_paths": 2,       # affiliate/adsense/ürün/sponsor...
    "min_ctr_pct": 4.0,           # 30 gün sonu CTR eşiği
    "min_retention_pct": 35.0,
    "go_video_velocity": "ilk 48 saatte niş-ortalaması üzeri izlenme hızı",
}


def stage1_find_niches(seed: str = "") -> str:
    return (
        f"GÖREV: Sıfırdan başlanabilecek KARLI YouTube/TikTok/IG nişleri bul"
        f"{(' (alan: ' + seed + ')') if seed else ''}.\n"
        "VERİ KAYNAĞI KULLAN (tahmin etme): YouTube arama/autocomplete, Reddit talep sinyalleri, "
        "Google Trends yönü (yükselen/düşen), niş CPM/RPM aralıkları.\n"
        "Her nişi şu kriterlere göre 10 üzerinden PUANLA (kanıtla):\n"
        "a) yüksek reklam geliri (CPM/RPM) b) yüksek izlenme talebi c) düşük/orta rekabet "
        "d) yüz göstermeden üretilebilirlik e) uzun-vade içerik çıkarılabilirlik.\n"
        "EN MANTIKLI 6 nişi ver (yeni başlayan için). Her niş için platform+format "
        "(YT-uzun/Shorts/TikTok-IG-dikey). evidence TEK kısa cümle (token tasarrufu — kesilmesin).\n"
        'SADECE GEÇERLİ JSON (markdown yok), KISA tut: {"niches":[{"name":"","scores":{"cpm":0,'
        '"demand":0,"competition":0,"faceless":0,"longevity":0},"total":0,"platform_format":"","evidence":""}],"top5":["..."]}'
    )


def stage2_validate(niche: str) -> str:
    t = THRESHOLDS
    return (
        f"GÖREV: '{niche}' nişini KARAR için analiz et (genel cevap YOK, sayısal).\n"
        "a) İnsanlar neden izliyor? b) Para nereden kazanılır (gelir yolları listesi)? "
        "c) Rakipler hangi formatı kullanıyor? d) Yeni kanal nereden farklılaşır? "
        "e) 6 ay sonra hâlâ izlenir mi (trend yönü)?\n"
        f"EŞİKLER: talep≥{t['min_demand_score']}/10, rekabet≤{t['max_competition_score']}/10, "
        f"gelir yolu≥{t['min_revenue_paths']}.\n"
        'Net KARAR ver. SADECE JSON: {"why_watched":"","revenue_paths":["..."],"competitor_format":"",'
        '"differentiation":"","longevity_6mo":"","demand_score":0,"competition_score":0,"decision":"GİR|GİRİLMEZ","reason":""}'
    )


def stage3_subniches(niche: str) -> str:
    return (
        f"GÖREV: '{niche}' için DÜŞÜK rekabet + TALEBİ olan 8 alt-niş (KOMPAKT — kesilmesin).\n"
        "Her alt-niş için KISA: hedef kitle, 3 video fikri, 1 başlık örneği, görsel tarz, "
        "platform+format, neden + talep (tek cümle).\n"
        'SADECE GEÇERLİ JSON (markdown yok, kısa): {"subniches":[{"name":"","audience":"",'
        '"video_ideas":["3 adet"],"title":"","visual_style":"","platform_format":"","why":""}]}'
    )


def stage4_competitor(niche: str) -> str:
    return (
        f"GÖREV: '{niche}' için rakip analizi + UYGULANABİLİR kanal başlangıç stratejisi.\n"
        "Büyük kanalların en çok izlenen videolarını incele: a) çalışan başlık formatları "
        "b) tekrar tekrar izlenen konular c) rakiplerin içerik AÇIKLARI d) yeni kanalın öne çıkış açısı "
        "e) ilk 30 günde test edilecek video fikirleri.\n"
        "KOMPAKT tut (kesilmesin): her liste max 5 madde, strateji 2-3 cümle.\n"
        'SADECE GEÇERLİ JSON (markdown yok): {"winning_title_formats":["max5"],"evergreen_topics":["max5"],'
        '"content_gaps":["max5"],"differentiation_angle":"","first_30d_tests":["max5"],"channel_start_strategy":""}'
    )


def stage5_plan(niche: str) -> str:
    t = THRESHOLDS
    return (
        f"GÖREV: '{niche}' için 30 GÜNLÜK tam başlangıç+test planı.\n"
        "a) 30 video fikri b) ilk 5 video başlığı c) thumbnail metinleri d) video sıralaması "
        "e) içerik üretim formatı g) günlük yapılacaklar h) başarı ölçüm kriterleri.\n"
        f"NET KILL/CONTINUE EŞİKLERİ koy: CTR≥%{t['min_ctr_pct']}, retention≥%{t['min_retention_pct']}, "
        f"izlenme-hızı ({t['go_video_velocity']}), abone hedefi. 30 gün sonu devam/bırak kararı net olsun.\n"
        'SADECE JSON: {"video_ideas_30":["..."],"first5_titles":["..."],"thumbnail_texts":["..."],'
        '"video_order":["..."],"production_format":"","daily_tasks":["..."],'
        '"success_thresholds":{"ctr_pct":0,"retention_pct":0,"subs":0},"continue_decision_rule":""}'
    )
