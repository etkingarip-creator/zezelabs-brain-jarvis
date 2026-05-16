import json
import os
import sys
import requests

# Proje köküne path ekle
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.mq_client import MQClient
from core.memory.db_client import TieredMemoryClient

class MysticInterpreter:
    def __init__(self):
        print("[Interpreter] ZOM Mystic Interpreter v1 başlatılıyor...")
        self.mq = MQClient()
        self.memory = TieredMemoryClient(collection_name="mystic_knowledge")
        self.bridge_url = os.getenv("JARVIS_BRIDGE_URL", "http://jarvis_bridge:7000/query")
    
    def interpret_symbols(self, task_desc):
        """
        Mistik, ezoterik veya sembolik analiz yapar.
        RAG kullanarak yerel bilgi bankasından beslenir.
        """
        # RAG Sorgusu
        print(f"[Interpreter] 🔍 Bilgi bankası taranıyor...")
        mem_results = self.memory.search_memory(task_desc, n_results=2)
        
        # Uzun süreli hafızadan (Chroma) gelen dökümanları ayıkla
        long_term_docs = mem_results.get("long_term", {}).get("documents", [[]])[0]
        context_str = "\n".join(long_term_docs) if long_term_docs else "Ek bilgi bulunamadı."
        
        system_prompt = (
            "Sen bir Zezelabs Mistik Analistisin (Mystic Interpreter). "
            "Gelen sembolik, astrolojik veya ezoterik soruları ZOM derinliğiyle analiz et.\n"
            "Aşağıdaki yerel bilgi bankası verilerini referans al:\n"
            f"--- BİLGİ BANKASI ---\n{context_str}\n---------------------\n\n"
            "Analiz şunları içermeli:\n"
            "1. SEMBOLİK ANLAM: Arketipler ve semboller.\n"
            "2. EZOTERİK YORUM: Gizli anlamlar.\n"
            "3. AKSİYON: Kullanıcının bu bilgiyi nasıl kullanabileceği."
        )
        
        try:
            print(f"[Interpreter] 🔮 Semboller yorumlanıyor...")
            payload = {
                "prompt": f"{system_prompt}\n\nGörev: {task_desc}",
                "model": "gemini-2.5-flash",
                "force_cloud": True
            }
            resp = requests.post(self.bridge_url, json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json().get("response", "Yorum üretilemedi.")
        except Exception as e:
            return f"Yorumlama sırasında hata: {e}"

    def process_task(self, ch, method, properties, body):
        data = json.loads(body)
        task_id = data.get("id")
        task_desc = data.get("task", "")
        
        print(f"\n[Interpreter] Görev #{task_id} için mistik analiz yapılıyor...")
        
        interpretation = self.interpret_symbols(task_desc)
        
        print(f"[Interpreter] ✅ Analiz tamamlandı.")
        
        # Sonucu orkestratöre gönder
        result_payload = {
            "id": task_id,
            "type": "mystic_analysis_completed",
            "task": task_desc,
            "interpretation": interpretation,
            "status": "mystic_ready"
        }
        
        self.mq.publish("main_orchestrator_queue", result_payload)
        print(f"[Interpreter] 📤 Mistik analiz orkestratöre iletildi.")

    def start(self):
        self.mq.connect()
        self.mq.declare_queue("mystic_queue")
        self.mq.consume("mystic_queue", self.process_task)

if __name__ == "__main__":
    agent = MysticInterpreter()
    agent.start()
