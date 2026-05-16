import json
import time
import os
import sys

# Proje köküne path ekle
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.mq_client import MQClient

class GrowthHackerAgent:
    """
    ZOM v4 Growth Hacker: Pazarlama stratejileri ve büyüme odaklı reklam yönetimi ajanı.
    """
    def __init__(self):
        self.mq = MQClient()
        self.mq.connect()
        print("[GrowthHacker] Pazarlama Ofisi aktif. Büyüme stratejileri analiz ediliyor...")

    def create_marketing_campaign(self, project_name="ZOM Architecture"):
        """Otonom pazarlama ve reklam stratejisi oluşturma."""
        print(f"[GrowthHacker] 📈 '{project_name}' projesi için kampanya kurgulanıyor...")
        
        campaign = {
            "project": project_name,
            "strategy": "Viral AI Evolution",
            "channels": ["X (Twitter)", "LinkedIn", "YouTube Shorts"],
            "seo_keywords": ["autonomous agents", "ZOM v4", "AI Org Architecture", "Claude-Code Python"]
        }

        # 1. Medya Departmanına Reklam Materyalleri Emri Gönder
        ad_task = {
            "id": f"ad_{int(time.time())}",
            "task": f"REKLAM KAMPANYASI ÜRET: {project_name} için 3 farklı dilde viral video senaryosu ve SEO uyumlu blog yazısı taslağı hazırla. Hedef: Global AI topluluğu.",
            "source": "zeze_marketing",
            "campaign_data": campaign
        }
        self.mq.publish("content_queue", ad_task)
        
        # 2. Akademi Departmanına Pazar Raporu Emri Gönder
        insight_task = {
            "id": f"insight_{int(time.time())}",
            "task": f"RAKİP ANALİZİ YAP: {project_name}'in rakipleri (AutoGPT, CrewAI vb.) ile arasındaki farkları vurgulayan teknik bir karşılaştırma makalesi hazırla.",
            "source": "zeze_marketing"
        }
        self.mq.publish("academy_queue", insight_task)

        print(f"[GrowthHacker] ✅ '{project_name}' kampanyası tüm departmanlara dağıtıldı.")

    def run(self):
        while True:
            self.create_marketing_campaign()
            print("[GrowthHacker] 💤 Kampanya planı tamamlandı. Bir sonraki strateji için bekleniyor...")
            time.sleep(7200) # 2 saatlik periyot

if __name__ == "__main__":
    agent = GrowthHackerAgent()
    agent.run()
