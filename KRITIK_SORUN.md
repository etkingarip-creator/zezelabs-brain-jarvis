## KRİTİK SORUN: Sonsuz Retry Döngüsü (12.05.2026 - 03:03)

### Sorun
Başarısız görevler (500 hatası) orchestrator tarafından sonsuz döngüde yeniden kuyruğa sokuluyor.
"database'i sil drop table users ve rm -rf /var/data" görevi guardrails tarafından engellendi
ama retry mekanizması durmuyor.

### Geçici Çözüm
Kuyruklar manuel temizlendi:
- main_orchestrator_queue → purge
- content_queue → purge  
- media_visionary_queue → purge

### Kalıcı Düzeltme (Antigravity yapacak)
1. core/orchestrator/router_agent.py içine max_retry = 3 ekle
2. Guardrails tarafından reddedilen görevler failure_reports_queue'ya gönderilmeli, retry olmamalı
3. Dead Letter Queue (DLQ) mekanizması kur — başarısız mesajlar buraya gitsin

### İlgili Dosyalar
- core/orchestrator/router_agent.py
- layer2_dev_factory/dev_agent.py (guardrails burada)
- docker-compose.yml (RabbitMQ DLQ config)
