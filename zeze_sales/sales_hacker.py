import json
import time
import os
import sys

# Proje köküne path ekle
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.mq_client import MQClient

class SalesHackerAgent:
    """
    ZOM v4 Sales Hacker: Lokal işletmeleri tarayan ve demo/teklif süreci yöneten ajan.
    """
    def __init__(self):
        self.mq = MQClient()
        self.mq.connect()
        print("[SalesHacker] Satış Ofisi aktif. Hedef işletmeler taranıyor...")

    def hunt_for_leads(self, sector="Restaurant"):
        """Lokal işletmeleri tarama (Simülasyon/Search)."""
        print(f"[SalesHacker] 🎯 '{sector}' sektöründe potansiyel müşteriler taranıyor...")
        
        # Simüle edilmiş lead listesi (Gerçekte SearchTool ile beslenir)
        leads = [
            {"name": "Zeze Burger Local", "url": "http://local-burger-test.com", "issue": "Mobil uyumluluk yok, online sipariş eksik."},
            {"name": "Mistik Kahve Evi", "url": "http://mistik-coffee.com", "issue": "SEO skoru çok düşük, Google Haritalar kaydı zayıf."}
        ]

        for lead in leads:
            print(f"[SalesHacker] 🔍 Lead Yakalandı: {lead['name']} ({lead['url']})")
            print(f"[SalesHacker] 🛠️ Sorun Tespiti: {lead['issue']}")
            
            # 1. Mühendislik Departmanına Demo Emri Gönder
            demo_task = {
                "id": f"demo_{int(time.time())}",
                "task": f"DEMO WEB SITESI TASARLA: {lead['name']} için modern, mobil uyumlu ve online sipariş destekli bir landing page prototipi oluştur. Mevcut sorun: {lead['issue']}",
                "source": "zeze_sales",
                "client": lead['name'],
                "attempt": 1
            }
            self.mq.publish("dev_queue", demo_task)
            
            # 2. Medya Departmanına Teklif Sunumu Emri Gönder
            proposal_task = {
                "id": f"prop_{int(time.time())}",
                "task": f"SATIŞ TEKLİFİ HAZIRLA: {lead['name']} işletmesi için profesyonel bir PDF teklif dosyası oluştur. İçerik: Sorun analizi, demo linki ve aylık bakım paketi fiyatlandırması.",
                "source": "zeze_sales"
            }
            self.mq.publish("content_queue", proposal_task)
            
            # 3. Telegram üzerinden CEO'ya bildirim gönder
            self.mq.publish("telegram_queue", {
                "message": f"🚀 [YENİ SATIŞ FIRSATI] {lead['name']} için otonom demo ve teklif süreci başlatıldı!\nEksik: {lead['issue']}"
            })

            print(f"[SalesHacker] ✅ {lead['name']} için tüm departmanlar tetiklendi.")
            time.sleep(2)

    def run(self):
        while True:
            self.hunt_for_leads()
            print("[SalesHacker] 💤 Lead taraması tamamlandı. 1 saat sonra yeni av başlatılacak...")
            time.sleep(3600)

if __name__ == "__main__":
    agent = SalesHackerAgent()
    agent.run()
