# 🧠 ZEZELABS DIGITAL HOLDING — Otonom AI Beyin Mimarisi

> **ZOM İlkesi:** Tulpar'ın yerel kaynaklarını (Local LLM & Local Vector DB) en verimli şekilde kullan.
> Gereksiz token harcamasından kaçın — kararlar net ve hızlı verilmeli.

---

## Mimari Genel Görünüm

```
[Görev Girişi]
      │
      ▼
┌──────────────────────────────┐
│  LAYER 1 — Orkestratör       │  main_orchestrator_queue dinler
│  RouterAgent → Yönlendirme  │  (dev / automation / content)
└───────────┬──────────────────┘
            │
     ┌──────┴──────┐
     ▼             ▼
┌─────────┐  ┌──────────────┐
│ LAYER 2 │  │   LAYER 3    │
│ Dev     │  │ Automation   │  n8n webhook / API çağrıları
│ Factory │  │ Agent        │
│─────────│  └──────────────┘
│dev_agent│◄─────────────────── reviewer feedback döngüsü
│reviewer │──► PR Özeti + squash merge hazırlığı
└────┬────┘
     │ memory_distillation_queue
     ▼
┌──────────────────────────────┐
│  LAYER 4 — Hafıza            │
│  Kısa: Redis (TTL: 1s)      │
│  Uzun: ChromaDB (Vektörel)  │
│  Distillation Loop          │
└──────────────────────────────┘
```

---

## Klasör Yapısı

| Dizin / Dosya | Açıklama |
|---|---|
| `core/mq_client.py` | Paylaşılan RabbitMQ istemcisi (retry, durable queue) |
| `layer1_orchestrator/` | Ana orkestratör + RouterAgent |
| `layer2_dev_factory/dev_agent.py` | ZOM Dev Agent: Git, Dockerize, 3-retry, guardrails |
| `layer2_dev_factory/reviewer_agent.py` | ZOM Reviewer: ast.parse, pylint ≥8, flake8, PR özeti |
| `layer3_automation/automation_agent.py` | n8n webhook entegrasyonu |
| `layer4_memory/db_client.py` | TieredMemoryClient: Redis + ChromaDB |
| `layer4_memory/distillation.py` | Öğrenme döngüsü — hata/başarı → ChromaDB |
| `docker-compose.yml` | Altyapı: RabbitMQ, ChromaDB, Redis, n8n |
| `requirements.txt` | Bağımlılıklar (pika, chromadb, redis, pylint, flake8…) |
| `test_publisher.py` | Sistemi uçtan uca test eden yayıncı |

---

## Güvenlik Kuralları (Guardrails)

- ❌ `rm -rf`, `drop table`, `mkfs` gibi tehlikeli komutlar **otomatik reddedilir**
- ❌ `api_key =`, `sk-`, `AKIA` gibi hardcoded secret pattern'ları **otomatik bloke edilir**
- ✅ Tüm gizli değerler `.env` üzerinden yönetilir; `.gitignore` zorunlu kontrol edilir

---

## Reviewer ZOM Standartları

| Kriter | Eşik |
|---|---|
| Pylint skoru | ≥ 8.0 / 10 |
| Syntax hatası | 0 (ast.parse ile kontrol) |
| Flake8 ihlali | Kayıt altına alınır, uyarı verilir |
| Dockerfile | Zorunlu |
| .env.example | Zorunlu |
| .gitignore (.env içermeli) | Zorunlu |

---

## Hızlı Başlangıç

### 1. Sistemi Başlat (Altyapı + Ajanlar)
```bash
docker-compose up -d --build
```

### 2. Test Gönder
```bash
python test_publisher.py
```

### 3. İzleme ve Loglar
```bash
# Tüm stack loglarını izle
docker-compose logs -f

# Sadece orkestratörü izle
docker logs -f zezelabs_orchestrator
```

### 4. AI Köprüsü (Jarvis Bridge)
Sistem, `zezelabs_bridge` (Port 7000) üzerinden akıllı yönlendirme yapar. Köprü kapalıysa veya hata verirse otomatik olarak **Keyword Fallback** mekanizması devreye girer.

### 5. İzleme
- **RabbitMQ Yönetim UI:** http://localhost:15672 (admin / admin123)
- **n8n Workflow:** http://localhost:5678
- **ChromaDB API:** http://localhost:8000

---

## Kuyruk Haritası

| Kuyruk | Yayıncı | Tüketici |
|---|---|---|
| `main_orchestrator_queue` | Test Publisher / Reviewers | Layer 1 Orkestratör |
| `dev_queue` | Orkestratör, Reviewer (revision) | Dev Agent |
| `reviewer_queue` | Dev Agent | Reviewer Agent |
| `automation_queue` | Orkestratör | Automation Agent |
| `content_queue` | Orkestratör | (Yakında) Content Agent |
| `memory_distillation_queue` | Dev / Reviewer | Distillation Loop |
| `failure_reports_queue` | Dev Agent (3. başarısızlık) | (Manuel inceleme) |

