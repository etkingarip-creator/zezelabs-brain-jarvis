import json
import hashlib
import os
import sys

# Proje köküne path ekle
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

class ZezePedia:
    """
    Zezelabs Kurumsal Hafızası (Token Saver).
    Sık kullanılan çözümleri ve pazar analizlerini önbelleğe alır.
    """
    def __init__(self, db_path="zeze_academy/zeze_pedia.json"):
        self.db_path = os.path.join(PROJECT_ROOT, db_path)
        self.memory = self._load_memory()
        print(f"[ZezePedia] Hafıza yüklendi: {len(self.memory)} kayıt mevcut.")

    def _load_memory(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_memory(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, indent=4, ensure_ascii=False)

    def get_knowledge(self, prompt: str):
        """Prompt'un hash'ini alıp hafızada ara."""
        p_hash = hashlib.md5(prompt.strip().lower().encode()).hexdigest()
        if p_hash in self.memory:
            print(f"[ZezePedia] 🎯 HIT! Token harcamadan hafızadan çekildi: {p_hash}")
            return self.memory[p_hash]
        return None

    def store_knowledge(self, prompt: str, response: str):
        """Yeni bilgiyi hafızaya kaydet."""
        p_hash = hashlib.md5(prompt.strip().lower().encode()).hexdigest()
        self.memory[p_hash] = {
            "prompt": prompt,
            "response": response,
            "timestamp": os.path.getmtime(self.db_path) if os.path.exists(self.db_path) else 0
        }
        self._save_memory()
        print(f"[ZezePedia] 💾 Yeni bilgi endekslendi: {p_hash}")

# Singleton Instance
pedia = ZezePedia()
