# Zeze-Academy Engine — The Autonomous Upskilling Platform

## USP'ler
1. Trace-driven autonomous curriculum
2. Model distillation cost control
3. Multi-tenant token budget guard
4. BYOK monetization
5. Value-based pricing
6. Nightly educator agent
7. Prompt/skill mutation with approval

## Kritik Güvenlik Kuralları
1. Müşteri trace verisi tenant izolasyonu olmadan karışmayacak.
2. PII/secret redaction olmadan eğitim datasına yazılmayacak.
3. Prompt mutation otomatik prod’a uygulanmayacak; önce approval required.
4. BYOK keyleri loglanmayacak.
5. Eğitim bütçesi aşılırsa freeze.
6. Distillation dataset JSONL olarak export edilecek ama secret içermeyecek.
7. Multi-tenant storage tenant_id zorunlu olacak.
8. Eğitim outputları rollback edilebilir olacak.

## Fazlar
Phase 0: Roadmap + architecture doc
Phase 1: Trace logger + curriculum generator skeleton
Phase 2: Budget guard + tenant isolation
Phase 3: Prompt mutation approval flow
Phase 4: Distillation dataset builder
Phase 5: Real training/fine-tune/export pipeline
