import json
import os
import sys
import time
# Proje köküne path ekle
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.mq_client import MQClient

# Layer 4 DB client'i ice aktar
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db_client import TieredMemoryClient

# Modul seviyesi tanimlama — main() tarafindan atanir
memory_client: TieredMemoryClient | None = None
mq: MQClient | None = None


def distill_and_store(event: dict, memory: TieredMemoryClient, mq_client: MQClient):
    """
    Gelen ham olayı (başarı/başarısızlık) analiz ederek öğrenme
    kaydı oluşturur ve ChromaDB'ye (uzun süreli hafıza) yazar.
    """
    event_type = event.get("type", "unknown")
    task = event.get("task", "")
    task_id = event.get("task_id", "?")

    if event_type == "success":
        score = event.get("pylint_score", "N/A")
        attempt = event.get("attempt", 1)
        distilled = (
            f"[BAŞARI] Görev '{task}' (ID:{task_id}) {attempt}. denemede tamamlandı. "
            f"Pylint skoru: {score}/10. "
            f"Öğrenilen: Dockerize + .env şablonu + atomic commit bu tür görevler için çalışır."
        )
        metadata = {
            "type": "success",
            "task_id": task_id,
            "pylint_score": str(score),
            "attempt": str(attempt),
            "timestamp": str(time.time()),
        }
        print(f"[Distillation] ✅ Başarı kaydı işleniyor: {distilled[:80]}...")
        memory.add_memory(distilled, metadata=metadata, tier="long")
        # Telegram'a bildir
        mq_client.publish("telegram_out_queue", {
            "type": "memory_update",
            "task": distilled,
            "id": task_id
        })

    elif event_type == "failure":
        feedback = event.get("feedback_history", "")
        distilled = (
            f"[BAŞARISIZLIK] Görev '{task}' (ID:{task_id}) 3 denemede tamamlanamadı. "
            f"Son geri bildirim: '{feedback}'. "
            f"Öğrenilen: Bu tür görevlerde reviewer kriterlerine dikkat et, "
            f"pylint skoru ve mimari dosyalar eksik olmamalı."
        )
        metadata = {
            "type": "failure",
            "task_id": task_id,
            "feedback": feedback[:200],
            "timestamp": str(time.time()),
        }
        print(f"[Distillation] ❌ Başarısızlık kaydı işleniyor: {distilled[:80]}...")
        memory.add_memory(distilled, metadata=metadata, tier="long")
        # Telegram'a bildir
        mq_client.publish("telegram_out_queue", {
            "type": "memory_update",
            "task": distilled,
            "id": task_id
        })

    else:
        # Bilinmeyen olay türü → kısa süreli hafızaya al
        raw_text = json.dumps(event)
        print(f"[Distillation] ℹ️ Bilinmeyen olay tipi '{event_type}', kısa süreli hafızaya alınıyor.")
        memory.add_memory(raw_text, metadata={"type": event_type}, tier="short")


def on_distillation_event(ch, method, properties, body):
    try:
        event = json.loads(body)
        print(f"\n[Distillation] Damıtma görevi alındı: {event.get('type')} | Task #{event.get('task_id')}")
        distill_and_store(event, memory_client, mq)
    except Exception as e:
        print(f"[Distillation] ❗ Hata: {e}")
        import traceback; traceback.print_exc()


def main():
    print("[Distillation] ZOM Öğrenme Döngüsü v2 başlatılıyor...")
    global memory_client, mq
    memory_client = TieredMemoryClient()
    mq = MQClient()
    mq.connect()
    mq.declare_queue("memory_distillation_queue")
    try:
        mq.consume("memory_distillation_queue", on_distillation_event)
    except KeyboardInterrupt:
        print("[Distillation] Kapatılıyor.")


if __name__ == "__main__":
    main()
