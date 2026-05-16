import json
import time
import os
import sys

# Proje köküne path ekle
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.mq_client import MQClient
from core.zeze_pedia import pedia

class AuditorAgent:
    """
    ZOM v5 Auditor: Tüm departmanların çıktısını denetleyen acımasız müfettiş.
    Kaliteyi onaylamazsa görevi ajana geri gönderir.
    """
    def __init__(self):
        self.mq = MQClient()
        self.mq.connect()
        print("[Auditor] Denetim Ofisi aktif. Tüm iş çıktıları mercek altında.")

    def on_review_request(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            agent_id = data.get("origin_agent", "unknown")
            task_id = data.get("task_id", "unknown")
            content = data.get("content", "")
            
            print(f"[Auditor] 🔎 {agent_id} tarafından yapılan '{task_id}' işi denetleniyor...")
            
            # --- ACIMASIZ DENETİM MANTIĞI (Simülasyon) ---
            # Gerçekte burada LLM veya statik analiz araçları çalışır
            is_perfect = True
            feedback = ""

            if len(content) < 50:
                is_perfect = False
                feedback = "İş içeriği çok sığ. Daha detaylı çalışma gerekiyor."
            
            if "TODO" in content or "FIXME" in content:
                is_perfect = False
                feedback = "Bitmemiş kod/içerik (TODO) teslim edilemez."

            if is_perfect:
                print(f"[Auditor] ✅ ONAYLANDI: {task_id}. İlgili birime/kuyruğa paslanıyor.")
                # Onaylanan işi final kuyruğuna veya müşteriye (Telegram) gönder
                self.mq.publish("telegram_queue", {
                    "message": f"✅ [İŞ ONAYLANDI] {agent_id} tarafından tamamlanan '{task_id}' işi denetimden geçti."
                })
            else:
                print(f"[Auditor] ❌ REDDEDİLDİ: {agent_id} -> {feedback}")
                
                # ── ZezePedia: Training Loop (Hatalardan Öğrenme) ──
                pedia.store_knowledge(f"error_pattern:{agent_id}", f"Red Sebebi: {feedback}")
                
                # Görevi ajana geri fırlat (Loopback)
                retry_task = data.get("original_task", {})
                retry_task["feedback"] = feedback
                retry_task["attempt"] = retry_task.get("attempt", 0) + 1
                
                # Ajanın kendi kuyruğuna geri gönder
                self.mq.publish(f"{agent_id}_queue", retry_task)
                print(f"[Auditor] 📤 Görev geri gönderildi: {agent_id}")

            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"[Auditor] Denetim Hatası: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def run(self):
        # Auditor 'reviewer_queue' kuyruğunu dinler
        self.mq.declare_queue("reviewer_queue")
        print(f"[Auditor] 👂 'reviewer_queue' dinleniyor...")
        self.mq.channel.basic_consume(queue="reviewer_queue", on_message_callback=self.on_review_request)
        self.mq.channel.start_consuming()

if __name__ == "__main__":
    agent = AuditorAgent()
    agent.run()
