import json
import time
import os
import sys

# Proje köküne path ekle
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.mq_client import MQClient

class BridgeAgent:
    """
    ZOM v4 Bridge Agent: Departmanlar arası veri paslaşma motoru.
    Örn: Finans verisini Medya görevine dönüştürür.
    """
    def __init__(self):
        self.mq = MQClient()
        self.mq.connect()
        print("[BridgeAgent] Başlatıldı. Departmanlar arası iletişim hattı aktif.")

    def on_event_received(self, ch, method, properties, body):
        try:
            event = json.loads(body)
            source = event.get("origin_agent", "unknown")
            task_id = event.get("task_id", "N/A")
            
            # --- SENARYO 1: Finans -> Medya Entegrasyonu ---
            if source == "fin_agent" and "profit" in str(event.get("message", "")):
                print(f"[BridgeAgent] 💰 Finans kazanç raporu yakalandı! Medya üretimi tetikleniyor...")
                
                media_task = {
                    "id": f"bridge_{int(time.time())}",
                    "task": f"Finansal Kazanç Raporu Videosu Hazırla: {event.get('message')}",
                    "source": "bridge_agent",
                    "attempt": 1
                }
                self.mq.publish("content_queue", media_task)
                print(f"[BridgeAgent] 📤 Medya görev emri gönderildi: task_{media_task['id']}")

            # --- SENARYO 2: Eng -> Academy (Bilgi Transferi) ---
            if source == "dev_agent" and "fix" in str(event.get("message", "")):
                print(f"[BridgeAgent] 🛠️ Mühendislik çözümü yakalandı! Akademi kütüphanesine ekleniyor...")
                academy_task = {
                    "id": f"bridge_edu_{int(time.time())}",
                    "task": f"Yeni Mühendislik Çözümünü Belgele: {event.get('message')}",
                    "source": "bridge_agent"
                }
                self.mq.publish("academy_queue", academy_task)

            # Her zaman ACK ver
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"[BridgeAgent] ❗ Hata: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def run(self):
        # Bridge agent telemetry_exchange üzerinden tüm trafiği dinler (Fanout)
        # Not: MQClient'da telemetry_exchange fanout olarak tanımlanmıştı.
        self.mq.channel.exchange_declare(exchange='telemetry_exchange', exchange_type='fanout', durable=True)
        result = self.mq.channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        self.mq.channel.queue_bind(exchange='telemetry_exchange', queue=queue_name)
        
        print(f"[BridgeAgent] 👂 Tüm holding trafiği (Live Matrix) dinleniyor...")
        self.mq.channel.basic_consume(queue=queue_name, on_message_callback=self.on_event_received)
        self.mq.channel.start_consuming()

if __name__ == "__main__":
    agent = BridgeAgent()
    agent.run()
