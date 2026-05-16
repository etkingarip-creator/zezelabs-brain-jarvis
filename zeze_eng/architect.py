import json
import os
import sys
import requests

# Proje köküne path ekle
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.mq_client import MQClient

class EngArchitect:
    def __init__(self):
        print("[Architect] ZOM Engineering Architect v1 başlatılıyor...")
        self.mq = MQClient()
        self.bridge_url = os.getenv("JARVIS_BRIDGE_URL", "http://jarvis_bridge:7000/query")
    
    def design_system(self, task_desc):
        """
        Görevin yazılım mimarisini tasarlar.
        """
        system_prompt = (
            "Sen bir Zezelabs Baş Mimarsın (Chief Architect). Gelen yazılım görevi için "
            "modern, ölçeklenebilir ve temiz bir mimari tasarım yap.\n"
            "Tasarım şunları içermeli:\n"
            "1. DOSYA YAPISI: Önerilen klasörler ve dosyalar.\n"
            "2. TEKNOLOJİ YIĞINI: Önerilen kütüphaneler.\n"
            "3. VERİ AKIŞI: Bileşenler arası haberleşme (MQ, REST vb.)."
        )
        
        try:
            print(f"[Architect] 🏗️ Mimari tasarlanıyor...")
            payload = {
                "prompt": f"{system_prompt}\n\nGörev: {task_desc}",
                "model": "gemini-2.5-flash",
                "force_cloud": True
            }
            resp = requests.post(self.bridge_url, json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json().get("response", "Mimari üretilemedi.")
        except Exception as e:
            return f"Mimari tasarım sırasında hata: {e}"

    def process_task(self, ch, method, properties, body):
        data = json.loads(body)
        task_id = data.get("id")
        task_desc = data.get("task", "")
        
        # Sadece büyük mimari görevleri veya kodlama öncesi hazırlık olarak çalışabilir
        # Şimdilik direkt orkestratörden 'architect' anahtar kelimesiyle tetiklenebilir
        
        print(f"\n[Architect] Görev #{task_id} için mimari çalışma başlıyor...")
        
        architecture = self.design_system(task_desc)
        
        print(f"[Architect] ✅ Tasarım hazır.")
        
        # Tasarımı Master Coder'a ilet
        result_payload = {
            "id": task_id,
            "type": "architecture_completed",
            "task": task_desc,
            "architecture": architecture,
            "status": "design_ready"
        }
        
        self.mq.publish("dev_queue", result_payload)
        print(f"[Architect] 📤 Mimari tasarım Dev Agent'a (dev_queue) iletildi.")

    def start(self):
        self.mq.connect()
        self.mq.declare_queue("eng_architect_queue")
        self.mq.consume("eng_architect_queue", self.process_task)

if __name__ == "__main__":
    agent = EngArchitect()
    agent.start()
