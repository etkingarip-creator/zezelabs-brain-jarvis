# 🗺️ ZEZELABS AUTOMATED HOLDING ARCHITECTURE MAP
**Proje Yapısı, Dosya Yolları ve Otonom Araçlar Rehberi**

Bu harita, **ZOM (Zezelabs Otonom Organizasyon) v6.7** mimarisini oluşturan tüm klasörleri, alt sistemleri, otonom arka plan süreçlerini, telemetri rotalarını ve kullanılan aktif araçları detaylandırmaktadır.

---

## 1. Proje Dizin Yapısı (Project Tree)

```text
c:\Users\Zezelabs2\.gemini\antigravity\scratch\zezelabs-brain
├── backend/                        # Jarvis Ana FastAPI Sunucusu & STT Motoru
│   ├── jarvis.py                   # Jarvis Core Brain, Lifespan Controller, Speech Processor
│   ├── QueryEngine.py              # Ajan Sorgu / Düşünme Motoru Şablonu
│   └── jarvis_zom_core.log         # Sistem çalışma log dosyaları
├── core/                           # ZOM Otonom Çekirdek Kütüphaneleri (Shared Core)
│   ├── orchestrator/               # Ajan Yönetimi & Durum Takipçisi
│   │   ├── main.py                 # Core Orchestrator Döngüsü
│   │   ├── router_agent.py         # Akıllı Görev Yönlendirici (Router)
│   │   └── state_manager.py        # Canlı Ajan Senkronizasyon Arayüzü
│   ├── security/                   # Güvenlik & Doğrulama Katmanı
│   │   └── guardrails.py           # Claude Code / ZOM Güvenlik Filtreleri (Bash/FS)
│   ├── tools/                      # Entegre CLI & Tarayıcı/Tarama Araçları
│   │   ├── cli_executor.py         # Sistem Komut Yürütücüsü (CLI Executor)
│   │   └── project_scanner.py      # Akıllı Proje Taraması & Ağaç Yapılandırıcı
│   ├── mq_client.py                # RabbitMQ Çift Yönlü İletişim İstemcisi
│   ├── voice_listener.py           # Always-On Ses Dinleyicisi (Whisper + Silero VAD)
│   └── zeze_pedia.py               # Ortak Bilgi Bankası (Knowledge Base)
├── frontend/                       # Jarvis Isometric War Room Arayüzü (Vite + WebSockets)
├── standalone_jarvis/              # İzole Çalıştırılabilir Jarvis Versiyonu Klasörü
├── scratch/                        # Geliştirme, Araçlar ve Yapılandırma Alanı
│   ├── hermes-agent/               # Nous Research Hermes Core Agent Repo (Main Brain)
│   │   ├── cli.py                  # Hermes CLI API Yürütücüsü
│   │   ├── gateway/                # FastAPI / HTTP API Gateway Modülü
│   │   └── .env                    # DeepSeek V4 API Yapılandırması (Purge & Route)
│   ├── configure_hermes.py         # Otonom Hermes Entegrasyon Betiği
│   └── test_gemini_models.py       # Bulut Zekası Modelleri Doğrulama Betiği
├── zeze_eng/                       # ZOM Mühendislik Departmanı Ajanı
│   ├── architect.py                # Mimar Ajan (Architect)
│   ├── auditor.py                  # Kalite & Güvenlik Denetleyicisi (Auditor)
│   ├── sovereign_coder.py          # Otonom Yazılımcı (Developer)
│   └── devops_agent.py             # Sunucu & Dağıtım Ajanı (DevOps)
├── zeze_media/                     # ZOM Medya / İçerik Üretim Ajanı
│   ├── visionary.py                # Kreatif Vizyoner
│   └── scriptwriter.py             # Senarist / Metin Yazarı Ajanı
├── zeze_fin/                       # ZOM Finans Departman Ajanı
├── zeze_sales/                     # ZOM Satış Departman Ajanı
├── zeze_marketing/                 # ZOM Pazarlama Departman Ajanı
├── zeze_strategy/                  # ZOM Holding Strateji Planlayıcı Ajanı
├── zeze_telegram/                  # ZOM Dış İletişim Bot Entegrasyon Modülü
├── docker-compose.yml              # Nuclear-Stable Docker Kapsayıcı Yapılandırması
├── GHOST_LAUNCHER.py               # Sıfır-Konsol "Hayalet Modu" Ajan Başlatıcısı
└── START_JARVIS.bat                # Backend + UI Eşzamanlı Windows Başlatma Kılavuzu
```

---

## 2. Otonom Çekirdek Araçlar (Tool Suite)

Jarvis ve ZOM Ajanları tarafından otonom olarak kullanılan tüm entegre araçlar ve işlevleri aşağıda listelenmiştir:

### A. Sistem & Terminal Araçları
1. **`BashTool` / `cli_executor.py`:**
   * **İşlev:** Sandbox denetimli veya yerel terminal komutlarını yürütür.
   * **Güvenlik:** Tehlikeli komutları (`rm -rf /`, `format`, vb.) engelleyen `Guardrails` ile korunur.
2. **`FileEditTool` (Patch / Multi-Replace):**
   * **İşlev:** Dosyalardaki belirli kod bloklarını komple dosyayı ezmeden akıllı diff yöntemiyle değiştirir.
3. **`FileReadTool` / `project_scanner.py`:**
   * **İşlev:** Proje kodlarını tarar, analiz eder ve ağaç yapısı oluşturur.

### B. Sinir Ağı & Telemetri Araçları
1. **`MQClient` (`mq_client.py`):**
   * **İşlev:** Ajanlar arası RabbitMQ tabanlı otonom veri iletimini sağlar.
2. **`publish_rabbitmq_event` (`jarvis.py`):**
   * **İşlev:** Hermes Agent ve Jarvis zeka geçişlerini (Telemetry) holding omurgasına `zom_telemetry_queue` üzerinden basar.

### C. Görüntü & Ses Araçları
1. **`Ear` / `voice_listener.py`:**
   * **İşlev:** Silero VAD (Ses Aktivite Algılama) ile mikrofondan gelen sesleri süzer ve `faster-whisper` ile anında metne çevirir.
2. **`EdgeTTS` (Text-to-Speech):**
   * **İşlev:** Jarvis'in düşündüğü yanıtları en doğal insan sesiyle seslendirir.

---

## 3. Otonom Arka Plan Servisleri (Lifespan Processors)

Jarvis başlatıldığı anda, backend sunucusu üzerinden insan müdahalesine gerek kalmadan arka planda otonom olarak çalıştırılan işlemler:

* **`purge_openclaw()` (Temizlik Servisi):**
  * Eski OpenClaw dizinlerini (`~/.openclaw`) ve RabbitMQ kuyruklarını kalıcı olarak imha eder.
* **`launch_hermes_gateway()` (Beyin Başlatıcı):**
  * Soket taraması yaparak `8642` nolu portun boşta olduğunu doğrular ve arka planda otonom olarak `hermes gateway` sunucusunu tetikler.
* **`system_stats_broadcaster()` (Telemetri Sunucusu):**
  * 5 saniyede bir işletim sisteminin CPU, Bellek ve Uptime istatistiklerini WebSockets üzerinden Canlı Arayüze (War Room) basar.

---

## 4. RabbitMQ Sinir Ağı Rotaları (Queue Routes)

| Kuyruk Adı | Gönderen | Alıcı | Görevi |
| :--- | :--- | :--- | :--- |
| `main_orchestrator_queue` | Jarvis UI / STT | `core.orchestrator` | Kullanıcı komutlarını ajana yönlendirme |
| `zom_telemetry_queue` | `Brain.think` | ZOM İzleme Paneli | Model başarı, hata ve token kullanım telemetrisi |
| `zeze_eng_queue` | Router | `zeze_eng.architect` | Mühendislik/Kodlama görevleri rotası |
| `zeze_media_queue` | Router | `zeze_media.visionary` | Kreatif / Video / Yazım görevleri rotası |
