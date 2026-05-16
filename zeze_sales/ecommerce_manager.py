import json
import time
import os
import sys

# Proje köküne path ekle
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.mq_client import MQClient
from core.zeze_pedia import pedia

class EcommerceManagerAgent:
    """
    ZOM v4 Ecommerce Manager: Etsy, Gumroad ve Printify süreçlerini yöneten otonom tüccar.
    """
    def __init__(self):
        self.mq = MQClient()
        self.mq.connect()
        print("[EcommerceManager] Dijital Mağaza Ofisi aktif. Pazaryeri entegrasyonu hazır.")

    def launch_digital_product(self, product_type="Digital Stickers"):
        """Başlangıçtan satışa ürün lansman süreci."""
        print(f"[EcommerceManager] 🚀 Yeni Ürün Lansmanı Başlatılıyor: {product_type}")
        
        # 1. TASARIM: Medya departmanına tasarım emri gönder
        design_task = {
            "id": f"design_{int(time.time())}",
            "task": f"ETSY İÇİN DİJİTAL ÜRÜN TASARLA: {product_type} konseptinde, yüksek çözünürlüklü 10'lu bir set oluştur. Format: PNG + PDF (Printable).",
            "source": "zeze_ecommerce"
        }
        self.mq.publish("content_queue", design_task)

        # 2. SEO & LİSTELEME: ZezePedia'dan anahtar kelimeleri çek veya oluştur
        seo_keywords = ["digital stickers", "goodnotes stickers", "planner aesthetic", "etsy best seller 2026"]
        product_description = f"Modern and minimalist {product_type} for your digital planners. High quality, ready to download."
        
        # 3. MOCKUP: Ürün fotoğrafları için medya departmanını tekrar tetikle
        mockup_task = {
            "id": f"mockup_{int(time.time())}",
            "task": f"PRODUCT MOCKUP OLUŞTUR: {product_type} için Etsy standartlarında 5 adet vitrin fotoğrafı hazırla. Printify şablonlarını kullan.",
            "source": "zeze_ecommerce"
        }
        self.mq.publish("content_queue", mockup_task)

        # 4. LANSMAN BİLDİRİMİ: CEO'ya (Sana) rapor ver
        report = {
            "message": f"🛍️ [ETSY LANSMAN HAZIR] '{product_type}' ürünü için tasarımlar, SEO açıklamaları ve anahtar kelimeler hazırlandı.\nMağaza: Zezelabs Digital Lab\nFiyat: $9.99\nDurum: Yayına Hazır."
        }
        self.mq.publish("telegram_queue", report)

        print(f"[EcommerceManager] ✅ '{product_type}' lansman operasyonu diğer departmanlara dağıtıldı.")

    def handle_customer_query(self, query):
        """Müşteri mesajlarına otonom cevap taslağı hazırlama."""
        print(f"[EcommerceManager] 📩 Yeni Müşteri Mesajı: {query}")
        # Burada LLM bridge kullanılabilir, şimdilik taslak:
        reply = "Hello! Thank you for your interest in Zezelabs products. Yes, our digital stickers are compatible with GoodNotes and all major PDF annotation apps. Best, ZOM Merchant."
        return reply

    def run(self):
        # Örnek lansman döngüsü
        while True:
            self.launch_digital_product()
            print("[EcommerceManager] 💤 Lansman tamamlandı. Yeni ürün araştırması yapılıyor...")
            time.sleep(14400) # 4 saatte bir yeni ürün lansmanı denemesi

if __name__ == "__main__":
    agent = EcommerceManagerAgent()
    agent.run()
