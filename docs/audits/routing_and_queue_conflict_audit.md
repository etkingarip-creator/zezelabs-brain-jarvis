# Routing & Queue Conflict Audit

## Mapping Configuration (`core/orchestrator/router_agent.py`)
- `app_factory`: app, todo, frontend, backend, webapp, saas
- `zeze_media`: video, resim, tasarim, medya, icerik, content, thumbnail, seo, youtube, script, reel, podcast
- `crypto`: finans, kripto, crypto, borsa, butce, budget, gelir, gider, binance, btc, eth, fiyat, takip
- `academy`: egitim, ogren, akademi, arastir, research, rapor, analiz, analysis, ozet, summary
- `mystic`: strateji, strategy, karar, vizyon, vision, roadmap, ezoterik, mystic, hedef, goal
- `zeze_aro`: satis, sales, pazarlama, marketing, musteri, crm, lead, funnel, client, outreach, teklif, proposal, kampanya, campaign, ads, pipeline
- `telegram`: telegram, bildirim, notification, mesaj, bot
- `general`: default fallback

## Conflicts & Observations
- `zeze_media` correctly routed to `zeze_media_queue`.
- `zeze_aro` correctly receives all sales/marketing.
- `crypto` correctly isolated from `academy` tasks like `rapor` and `budget`.
- **Unknown tasks**: correctly fallback to `general` queue.
