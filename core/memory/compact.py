import requests
import tiktoken
import os

JARVIS_BRIDGE_URL = os.getenv("JARVIS_BRIDGE_URL", "http://zezelabs_bridge:7000/query")

class ContextCompactor:
    """
    ZOM v4 Context Compaction (Clawde_Code /compact muadili).
    Sadece yerel LLM (Ollama) kullanir.
    """
    def __init__(self, token_limit: int = 80000):
        self.token_limit = token_limit
        self.encoder = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        return len(self.encoder.encode(text))

    def needs_compaction(self, messages: list) -> bool:
        total_tokens = sum(self.count_tokens(m.get("content", "")) for m in messages)
        return total_tokens > self.token_limit

    def compact(self, messages: list, retain_recent: int = 5) -> list:
        total_tokens = sum(self.count_tokens(m.get("content", "")) for m in messages)
        if total_tokens <= self.token_limit or len(messages) <= retain_recent:
            return messages
            
        print(f"[COMPACT] Hafiza limiti asildi ({total_tokens}/{self.token_limit} tokens). Yerel Ollama ile sikistirma (distillation) baslatiliyor...")
        
        old_messages = messages[:-retain_recent]
        recent_messages = messages[-retain_recent:]
        
        old_text = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in old_messages])
        
        prompt = (
            "Asagidaki teknik konusma gecmisini; alinan teknik kararlar, karsilasilan hatalar ve su anki kodun durumu "
            "kalacak sekilde cok kisa, net ve maddeler halinde (maks 300 kelime) Turkce bir durumsam ozetine donustur:\n\n"
            f"{old_text[:40000]}" 
        )
        
        try:
            # ZOM Doktrini: Compact islemi stratejik degildir, OLLAMA kullanilir.
            payload = {
                "prompt": prompt,
                "force_cloud": False, 
                "use_cache": False
            }
            resp = requests.post(JARVIS_BRIDGE_URL, json=payload, timeout=120)
            if resp.status_code == 200:
                summary = resp.json().get("response", "")
                
                compacted_history = [
                    {"role": "system", "content": f"--- ONCEKI OLAYLARIN OZETI (COMPACTED) ---\n{summary}\n-----------------------------------------"}
                ]
                compacted_history.extend(recent_messages)
                
                new_tokens = sum(self.count_tokens(m.get("content", "")) for m in compacted_history)
                print(f"[COMPACT] Basarili! Eski baglam silindi. Yeni boyut: {new_tokens} tokens (Tasarruf: {total_tokens - new_tokens} tokens).")
                return compacted_history
        except Exception as e:
            print(f"[COMPACT] Ollama ozetleme hatasi: {e}. Guvenli moda geciliyor (eski mesajlar silinecek).")
            
        # Eger Ollama yillar once cokmusse veya baglanamazsa, sadece gecmisi sil (hard-trim)
        return messages[-retain_recent:]
