import json
import os
import sys
import requests

# Proje köküne path ekle
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.mq_client import MQClient

class AcademyEducator:
    def __init__(self):
        print("[Educator] ZOM Academy Educator v1 başlatılıyor...")
        self.mq = MQClient()
        self.bridge_url = os.getenv("JARVIS_BRIDGE_URL", "http://jarvis_bridge:7000/query")
    
    def generate_curriculum(self, research_data, task_desc):
        """
        Araştırma verilerini kullanarak bir eğitim müfredatı oluşturur.
        """
        system_prompt = (
            "Sen bir Zezelabs Eğitim Uzmanısın. Gelen araştırma verilerini kullanarak "
            "anlaşılır, adım adım bir eğitim müfredatı (curriculum) oluştur.\n"
            "Format: Giriş, Modül 1, Modül 2, ... Özet ve Quiz soruları."
        )
        
        try:
            print(f"[Educator] 🎓 Müfredat oluşturuluyor...")
            payload = {
                "prompt": f"{system_prompt}\n\nAraştırma Verileri:\n{research_data}\n\nOrijinal Görev: {task_desc}",
                "model": "gemini-2.5-flash",
                "force_cloud": True
            }
            resp = requests.post(self.bridge_url, json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json().get("response", "Müfredat üretilemedi.")
        except Exception as e:
            return f"Müfredat üretimi sırasında hata: {e}"

    def process_task(self, ch, method, properties, body):
        data = json.loads(body)
        task_id = data.get("id")
        research_data = data.get("research_data", "")
        task_desc = data.get("task", "")
        
        print(f"\n[Educator] Görev #{task_id} için müfredat hazırlanıyor...")
        
        curriculum = self.generate_curriculum(research_data, task_desc)
        
        print(f"[Educator] ✅ Müfredat hazır.")
        
        # Sonucu Technical Writer'a veya ana sisteme gönder
        result_payload = {
            "id": task_id,
            "type": "education_completed",
            "task": task_desc,
            "curriculum": curriculum,
            "status": "education_done"
        }
        
        # Şimdilik ana sisteme dönelim
        self.mq.publish("main_orchestrator_queue", result_payload)
        print(f"[Educator] 📤 Final eğitim içeriği orkestratöre iletildi.")

    def start(self):
        self.mq.connect()
        self.mq.declare_queue("academy_educator_queue")
        self.mq.consume("academy_educator_queue", self.process_task)

if __name__ == "__main__":
    agent = AcademyEducator()
    agent.start()
