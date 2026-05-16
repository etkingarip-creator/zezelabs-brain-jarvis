import json
import os
import sys
import requests

# Proje köküne path ekle
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.mq_client import MQClient

class AutomationAgent:
    def __init__(self):
        print("[Automation] ZOM Automation Agent v2 başlatılıyor...")
        self.mq = MQClient()
        self.webhook_url = os.getenv("N8N_WEBHOOK_URL", "http://zezelabs_n8n:5678/webhook/test-trigger")
    
    def trigger_n8n(self, task_data):
        """
        Görevin tipine göre ilgili n8n workflow'unu tetikler.
        """
        task_type = task_data.get("type", "generic")
        
        # Farklı operasyonlar için farklı endpoint'ler
        endpoints = {
            "media_pack_completed": os.getenv("N8N_MEDIA_WEBHOOK", self.webhook_url),
            "code_completed": os.getenv("N8N_GITHUB_WEBHOOK", self.webhook_url),
            "mystic_ready": os.getenv("N8N_MYSTIC_WEBHOOK", self.webhook_url),
            "generic": self.webhook_url
        }
        
        target_url = endpoints.get(task_type, self.webhook_url)
        
        try:
            print(f"[Automation] 🚀 n8n tetikleniyor ({task_type}) -> {target_url}")
            resp = requests.post(target_url, json=task_data, timeout=10)
            resp.raise_for_status()
            return True
        except Exception as e:
            print(f"[Automation] ⚠️ n8n hatası: {e}")
            # Fallback: Log to console in case of failure
            return False

    def process_task(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            task_id = data.get("id", "unknown")
            task_desc = data.get("task", "")
            
            print(f"\n[Automation] Görev #{task_id} için operasyonel süreç başlatıldı: {task_desc}")
            
            success = self.trigger_n8n(data)
            
            if success:
                print(f"[Automation] ✅ Operasyonel tetikleme başarılı.")
                # Telegram'a rapor gönder
                self.mq.publish("telegram_out_queue", {
                    "type": "report",
                    "task": f"Operasyon başarıyla tamamlandı: {task_desc}",
                    "id": task_id
                })
            else:
                print(f"[Automation] ❌ Operasyonel tetikleme başarısız. (Mock/Log modu aktif)")
                
        except Exception as e:
            print(f"[Automation] İşleme hatası: {e}")

    def start(self):
        self.mq.connect()
        self.mq.declare_queue("automation_queue")
        self.mq.consume("automation_queue", self.process_task)

if __name__ == "__main__":
    agent = AutomationAgent()
    agent.start()
