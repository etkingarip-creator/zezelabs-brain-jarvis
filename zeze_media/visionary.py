import json
import os
import sys
import requests

# Proje köküne path ekle
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.mq_client import MQClient

class MediaVisionary:
    def __init__(self):
        print("[Visionary] ZOM Media Visionary v1 başlatılıyor...")
        self.mq = MQClient()
        self.bridge_url = os.getenv("JARVIS_BRIDGE_URL", "http://jarvis_bridge:7000/query")
    
    def generate_visual_prompts(self, script):
        """
        Senaryo içeriğine uygun Midjourney/DALL-E promptları üretir.
        """
        system_prompt = (
            "Sen bir Zezelabs Görsel Tasarım Uzmanısın (Visionary). "
            "Gelen senaryo bölümleri için Midjourney v6 ve DALL-E 3 formatında "
            "sanatsal, hiper-gerçekçi veya stilize görsel promptları üret.\n"
            "Format: [Bölüm Adı] -> Prompt."
        )
        
        try:
            print(f"[Visionary] 🎨 Görsel promptlar üretiliyor...")
            payload = {
                "prompt": f"{system_prompt}\n\nSenaryo:\n{script}",
                "model": "gemini-2.5-flash",
                "force_cloud": True
            }
            resp = requests.post(self.bridge_url, json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json().get("response", "Promptlar üretilemedi.")
        except Exception as e:
            return f"Prompt üretimi sırasında hata: {e}"

    def process_task(self, ch, method, properties, body):
        data = json.loads(body)
        task_id = data.get("id")
        script = data.get("script", "")
        task_desc = data.get("task", "")
        
        print(f"\n[Visionary] Görev #{task_id} için görseller tasarlanıyor...")
        
        visual_prompts = self.generate_visual_prompts(script)
        
        print(f"[Visionary] ✅ Görsel plan hazır.")
        
        # Sonucu orkestratöre veya n8n otomasyonuna gönder
        result_payload = {
            "id": task_id,
            "type": "media_pack_completed",
            "task": task_desc,
            "script": script,
            "visual_prompts": visual_prompts,
            "status": "media_ready"
        }
        
        self.mq.publish("main_orchestrator_queue", result_payload)
        print(f"[Visionary] 📤 Medya paketi orkestratöre iletildi.")

    def start(self):
        self.mq.connect()
        self.mq.declare_queue("media_visionary_queue")
        self.mq.consume("media_visionary_queue", self.process_task)

if __name__ == "__main__":
    agent = MediaVisionary()
    agent.start()
