import json
import time
import os
import sys

# Proje köküne path ekle
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.mq_client import MQClient

class VisionaryAgent:
    """
    ZOM v6.0 Visionary Agent: Jarvis'in stratejik beyni.
    Sadece analiz yapmaz, projeleri acımasızca eleştirir ve Unicorn seviyesi için doping planlar.
    """
    def __init__(self):
        self.mq = MQClient()
        self.mq.connect()
        print("[VisionaryAgent] Konsey Odası hazır. Geleceği yaratmaya başlıyoruz.")

    def brutal_critique(self, project_data):
        """Projeyi acımasızca eleştiren Shadow CEO mantığı."""
        print(f"[VisionaryAgent] 💀 Acımasız Eleştiri Başlatıldı...")
        # Burada Antigravity'nin eleştiri promptları simüle edilir
        critique = "1. Pasif kullanıcı deneyimi.\n2. Network effect eksikliği.\n3. Monetizasyon sığlığı."
        return critique

    def plan_unicorn_doping(self, project_data):
        """Projeyi Unicorn seviyesine taşıyacak doping planı."""
        print(f"[VisionaryAgent] 🦄 Unicorn Doping Planlanıyor...")
        plan = "1. Bio-Sync (Health Data).\n2. Social Resonance (Guilds).\n3. Rare Collectibles (IAP)."
        return plan

    def analyze_market_and_assign(self):
        """
        2026 Pazar Trendleri Analizi (Simülasyon).
        CEO-level strategic depth: Geleceği öngör ve onu inşa ederek yarat.
        """
        print("[VisionaryAgent] 🔭 2026 Gelecek Vizyonu Taraması Başlatıldı...")
        
        # Shadow CEO'nun belirlediği 2026 Fırsat Alanları
        opportunities = [
            {
                "sector": "AI Infrastructure",
                "trend": "Multi-agent autonomous systems (ZOM gibi)",
                "action": "dev_queue",
                "task": "Ajanlar arası veri şifreleme protokolünü (TLS 2.0) optimize et."
            },
            {
                "sector": "Fintech / RWA",
                "trend": "Real-World Asset tokenization (Emlak tokenlaştırma)",
                "action": "fin_queue",
                "task": "Emlak endeksli token (REIT) için bir risk analizi ve portföy botu tasarla."
            },
            {
                "sector": "Media / Content",
                "trend": "Short-form AI video (TikTok/Reels dominance)",
                "action": "content_queue",
                "task": "Günde 10 tane AI tabanlı kısa içerik üretecek bir pipeline kur."
            }
        ]

        for opp in opportunities:
            print(f"[StrategyAnalyst] ✨ Fırsat Tespit Edildi: {opp['sector']} -> {opp['trend']}")
            
            task_payload = {
                "id": f"strat_{int(time.time())}_{opp['sector'][:3].lower()}",
                "task": opp["task"],
                "source": "zeze_strategy",
                "priority": "HIGH",
                "attempt": 1
            }
            
            # Görevi ana orkestratöre değil, doğrudan ilgili kuyruğa pasla (Shadow CEO yetkisiyle)
            self.mq.publish(opp["action"], task_payload)
            print(f"[StrategyAnalyst] 📤 Emir Gönderildi -> {opp['action']}: {opp['task'][:50]}...")
            time.sleep(1)

    def run(self):
        # Strateji analisti periyodik olarak çalışır (örn: her günün başlangıcında)
        while True:
            self.analyze_market_and_assign()
            print("[StrategyAnalyst] 💤 Analiz tamamlandı. Bir sonraki tarama için bekleniyor...")
            time.sleep(3600) # Saatlik tarama

if __name__ == "__main__":
    analyst = MarketStrategyAnalyst()
    analyst.run()
