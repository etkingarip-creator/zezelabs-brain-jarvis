import json
import os
import sys
import time
from duckduckgo_search import DDGS  # pyrefly: ignore[missing-import]

# Proje köküne path ekle
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.mq_client import MQClient

class AcademyResearcher:
    def __init__(self):
        print("[Researcher] ZOM Academy Researcher v1 başlatılıyor...")
        self.mq = MQClient()
        self.ddgs = DDGS()
    
    def search_and_synthesize(self, query):
        """
        DuckDuckGo üzerinden arama yapar ve sonuçları özetler.
        """
        print(f"[Researcher] 🔍 İnternette araştırılıyor: {query}")
        try:
            results = self.ddgs.text(query, max_results=5)
            synthesis = "\n".join([f"- {r['title']}: {r['body']} ({r['href']})" for r in results])
            return synthesis if synthesis else "Hiçbir sonuç bulunamadı."
        except Exception as e:
            return f"Arama sırasında hata oluştu: {e}"

    def process_task(self, ch, method, properties, body):
        data = json.loads(body)
        task_id = data.get("id")
        task_desc = data.get("task", "")
        
        print(f"\n[Researcher] Görev #{task_id} Alındı: {task_desc}")
        
        # Araştırma yap
        research_data = self.search_and_synthesize(task_desc)
        
        print(f"[Researcher] ✅ Araştırma tamamlandı.")
        
        # Sonucu Educator'a veya Dokümantasyon kuyruğuna gönder
        # Şimdilik direkt orkestratöre "completed" olarak dönelim veya bir sonraki adıma iletelim
        result_payload = {
            "id": task_id,
            "type": "research_completed",
            "task": task_desc,
            "research_data": research_data,
            "status": "research_done"
        }
        
        # Burada bir sonraki ajan Educator olmalı
        self.mq.publish("academy_educator_queue", result_payload)
        print(f"[Researcher] 📤 Bilgiler Educator'a (academy_educator_queue) iletildi.")

    def start(self):
        self.mq.connect()
        self.mq.declare_queue("academy_queue")
        self.mq.declare_queue("academy_educator_queue")
        self.mq.consume("academy_queue", self.process_task)

if __name__ == "__main__":
    agent = AcademyResearcher()
    agent.start()
