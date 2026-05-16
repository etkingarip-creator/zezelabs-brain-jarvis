import json
import os
import sys
import requests

# Proje köküne path ekle
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.mq_client import MQClient

class MediaScriptwriter:
    def __init__(self):
        print("[Scriptwriter] ZOM Media Scriptwriter v1 başlatılıyor...")
        self.mq = MQClient()
        self.bridge_url = os.getenv("JARVIS_BRIDGE_URL", "http://jarvis_bridge:7000/query")
    
    def write_script(self, task_desc):
        """
        YouTube veya Sosyal Medya için senaryo yazar.
        """
        system_prompt = (
            "Sen bir Zezelabs Medya Senaristisin. YouTube kanallarımız için "
            "izleyiciyi tutan (retention), etkileyici ve ZOM standartlarında senaryolar yaz.\n"
            "Senaryo yapısı:\n"
            "1. HOOK: İlk 5 saniye.\n"
            "2. INTRO: Merak uyandırıcı giriş.\n"
            "3. BODY: Bilgi dolu ana bölüm.\n"
            "4. OUTRO: CTA (Call to Action)."
        )
        
        try:
            print(f"[Scriptwriter] ✍️ Senaryo yazılıyor...")
            payload = {
                "prompt": f"{system_prompt}\n\nGörev: {task_desc}",
                "model": "gemini-2.5-flash",
                "force_cloud": True
            }
            resp = requests.post(self.bridge_url, json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json().get("response", "Senaryo üretilemedi.")
        except Exception as e:
            return f"Senaryo yazımı sırasında hata: {e}"

    def process_task(self, ch, method, properties, body):
        data = json.loads(body)
        task_id = data.get("id")
        task_desc = data.get("task", "")
        
        print(f"\n[Scriptwriter] Görev #{task_id} Alındı: {task_desc}")
        
        script = self.write_script(task_desc)
        
        print(f"[Scriptwriter] ✅ Senaryo tamamlandı.")
        
        # Görsel promptlar için Visionary'ye gönder
        result_payload = {
            "id": task_id,
            "type": "script_completed",
            "task": task_desc,
            "script": script,
            "status": "script_done"
        }
        
        self.mq.publish("media_visionary_queue", result_payload)
        print(f"[Scriptwriter] 📤 Senaryo Visionary'ye (media_visionary_queue) iletildi.")

    def start(self):
        self.mq.connect()
        self.mq.declare_queue("content_queue") # Eski adıyla content_queue'dan alabiliriz
        self.mq.declare_queue("media_visionary_queue")
        self.mq.consume("content_queue", self.process_task)

if __name__ == "__main__":
    agent = MediaScriptwriter()
    agent.start()
