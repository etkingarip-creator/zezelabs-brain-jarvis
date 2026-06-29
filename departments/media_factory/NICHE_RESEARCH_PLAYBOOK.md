# 🎯 Niş Araştırma Playbook — media_factory (Tüm AI Çalışanlar Uyar)

> **Vizyon:** Profesyoneller nişi **tahmin ederek** seçmez.
> 1. Önce **talebi ölçer** → 2. Sonra **rekabeti inceler** → 3. En son **üretim sistemini kurar.**
> Platformlar: YouTube (uzun + Shorts), TikTok, Instagram (dikey/yatay/uzun).

Bu playbook `niche_research_playbook.py` olarak kodda; `agent.run_niche_research()` ile çalıştırılır.
Direktif `domain_expertise` üzerinden **her AI çalışanın her LLM çağrısına** enjekte edilir.

---

## Aşama 1 — Talep Ölç (karlı niş bul)
Gerçek kaynak kullan (tahmin yok): YouTube arama/autocomplete, Reddit talep sinyalleri, Google Trends yönü, niş CPM/RPM.
Her nişi **10 üzerinden** puanla (kanıtla): reklam geliri · izlenme talebi · düşük/orta rekabet · yüz-göstermeden üretilebilirlik · uzun-vade.
→ En iyi **5 niş** + her birine **platform+format** eşle.

## Aşama 2 — Rekabeti İncele (gir/girilmez)
Her niş için: neden izleniyor · gelir yolları · rakip formatı · farklılaşma · 6-ay sürdürülebilirlik.
**Sayısal eşik:** talep ≥6/10, rekabet ≤6/10, gelir yolu ≥2.
→ Net **GİR / GİRİLMEZ** kararı (muğlak cevap yok).

## Aşama 3 — Alt-Niş (düşük rekabet + talep)
10 alt-niş; her biri: hedef kitle · 10 video fikri · 5 başlık · thumbnail açısı · görsel tarz · gelir potansiyeli · neden · **platform+format + talep kanıtı.**

## Aşama 4 — Rakip Analizi → Başlangıç Stratejisi
Çalışan başlık formatları · evergreen konular · **içerik açıkları** · öne-çıkış açısı · ilk-30-gün test fikirleri · izlenme-hızı (view velocity).
→ Doğrudan **uygulanabilir kanal başlangıç stratejisi.**

## Aşama 5 — 30 Günlük Test Planı
30 video fikri · ilk 5 başlık · thumbnail metinleri · video sırası · üretim formatı · günlük yapılacaklar.
**Net kill/continue eşikleri:** CTR ≥%4 · retention ≥%35 · izlenme-hızı niş-ortalaması üzeri · abone hedefi.
→ 30 gün sonu **devam/bırak** kararı net.

---

## Geliştirmeler (orijinal 5 prompta eklenenler)
- Gerçek **veri kaynağı** zorunluluğu (tahmin → ölçüm)
- Her aşamada **sayısal eşik** + JSON çıktı şeması (otomasyona uygun)
- **Platform/format eşlemesi** (YT-uzun/Shorts/TikTok-IG-dikey)
- **İzlenme-hızı** (view velocity) ve **net kill/continue** metrikleri
