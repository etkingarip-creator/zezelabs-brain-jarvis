import os
import sys
import uuid

# Proje köküne path ekle
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.memory.db_client import TieredMemoryClient

def seed_mystic_knowledge():
    """
    Zezelabs Mystic departmanı için temel bilgileri ve Tulpar Lore'unu ChromaDB'ye yükler.
    """
    memory = TieredMemoryClient(collection_name="mystic_knowledge")
    
    knowledge_base = [
        {
            "text": "Tulpar: Türk mitolojisinde kanatlı at arketiplerinden biridir. Zezelabs için Tulpar, hız, otonomi ve göksel zekayı temsil eder. Otonom ajanlarımızın 'hız ve sadakat' sembolüdür.",
            "metadata": {"category": "lore", "subject": "tulpar"}
        },
        {
            "text": "Numeroloji - 2026 Yılı: Numerolojik olarak 2026 yılı (2+0+2+6=10 -> 1) 'Yeni Başlangıçlar' ve 'Liderlik' yılıdır. ZOM v3'ün global genişleme evresiyle uyumludur.",
            "metadata": {"category": "numerology", "year": "2026"}
        },
        {
            "text": "Hermetik İlkeler: 'Yukarıda ne varsa, aşağıda da o vardır.' Bu ilke ZOM mimarisindeki fraktal yapıyı açıklar; her ajan kendi içinde bir orkestratör barındırır.",
            "metadata": {"category": "hermeticism", "principle": "correspondence"}
        },
        {
            "text": "Ezoterik Yazılım: Kod sadece bir komut dizisi değil, dijital evrende bir sigil (mühür) işlevi görür. Temiz kod, akışın (flow) engellenmemesini sağlar.",
            "metadata": {"category": "philosophy", "subject": "coding"}
        }
    ]
    
    print("[MysticKB] Veriler ChromaDB'ye yükleniyor...")
    for item in knowledge_base:
        memory.add_memory(item["text"], metadata=item["metadata"], tier="long")
    
    print("[MysticKB] ✅ Başarıyla yüklendi.")

if __name__ == "__main__":
    seed_mystic_knowledge()
