import json
import time
import os
import sys
import subprocess

# Proje köküne path ekle
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.mq_client import MQClient

class DevOpsAgent:
    """
    ZOM v4 DevOps Agent: Kendi kendini tamir eden altyapı motoru.
    Konteyner ve süreç sağlığını izler, gerekirse müdahale eder.
    """
    def __init__(self):
        self.mq = MQClient()
        self.mq.connect()
        self.last_seen = {} # Ajanların son görülme zamanları
        print("[DevOpsAgent] Başlatıldı. Altyapı koruma kalkanı devrede.")

    def on_telemetry(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            agent_id = data.get("origin_agent", "unknown")
            timestamp = data.get("timestamp", time.time())
            
            # Ajanı 'canlı' olarak işaretle
            self.last_seen[agent_id] = timestamp
            
            # Hata mesajı varsa analiz et
            message = str(data.get("message", "")).lower()
            if "error" in message or "fail" in message or "500" in message:
                print(f"[DevOpsAgent] 🚨 KRİTİK HATA YAKALANDI: {agent_id} -> {message}")
                self.heal_agent(agent_id, message)

            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"[DevOpsAgent] İzleme Hatası: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def heal_agent(self, agent_id, reason):
        """Kendi kendini tamir mekanizması."""
        print(f"[DevOpsAgent] 🛠️ {agent_id} için tamir protokolü başlatılıyor. Sebep: {reason}")
        
        # 1. Telegram'a bildir
        self.mq.publish("telegram_queue", {
            "message": f"🤖 [DevOps Müdahale] {agent_id} bir sorun yaşadı ve otomatik tamir ediliyor.\nSebep: {reason[:100]}"
        })

        # 2. Teknik müdahale (Docker restart simülasyonu / Subprocess denemesi)
        # Gerçek ortamda: subprocess.run(["docker", "restart", f"zeze_{agent_id}"])
        print(f"[DevOpsAgent] [SIM] Konteyner 'zeze_{agent_id}' yeniden başlatma emri gönderildi.")
        
        # 3. Kayıtlara geç
        self.mq.publish("failure_reports_queue", {
            "task_id": "HEAL_EVENT",
            "status": "HEALED",
            "agent": agent_id,
            "action": "AUTO_RESTART"
        })

    def run(self):
        # Telemetry exchange üzerinden tüm trafiği dinler
        self.mq.channel.exchange_declare(exchange='telemetry_exchange', exchange_type='fanout', durable=True)
        result = self.mq.channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        self.mq.channel.queue_bind(exchange='telemetry_exchange', queue=queue_name)
        
        print(f"[DevOpsAgent] 👂 Altyapı sağlığı izleniyor...")
        self.mq.channel.basic_consume(queue=queue_name, on_message_callback=self.on_telemetry)
        self.mq.channel.start_consuming()

if __name__ == "__main__":
    agent = DevOpsAgent()
    agent.run()
