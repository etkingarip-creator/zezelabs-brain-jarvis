"""
ZOM Kademeli Hafıza Sistemi (Tiered Memory)
────────────────────────────────────────────
• Kısa Süreli  → Redis  (hızlı, geçici, LRU temizlik)
• Uzun Süreli  → ChromaDB (kalıcı vektörel arama)

ZOM İlkesi: Gereksiz token harcamasından kaçın.
Yeni görevde önce hafızaya bak, yoksa hesapla.
"""
import uuid
import time
import json
import requests as _requests

try:
    import redis
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False

# ChromaDB: direkt HTTP ile baglaniyor (paket uyumsuzluklari olmadan)
_CHROMA_AVAILABLE = True  # requests zaten yuklu

SHORT_TERM_TTL = 3600        # 1 saat (saniye) — Redis'te tutma süresi
SHORT_TERM_THRESHOLD = 50    # Redis'te maksimum key sayısı — aşınca uyarı ver


class TieredMemoryClient:
    """
    ZOM Kademeli Hafıza İstemcisi.
    Tüm Layer 4 işlemleri bu sınıf üzerinden yürütülür.
    """

    def __init__(
        self,
        redis_host: str = None,
        redis_port: int = None,
        chroma_host: str = None,
        chroma_port: int = None,
        collection_name: str = "zezepedia",
    ):
        import os
        # Env vars prioritized
        redis_host = os.getenv("REDIS_HOST", redis_host or "redis")
        redis_port = int(os.getenv("REDIS_PORT", redis_port or 6379))
        chroma_host = os.getenv("CHROMA_HOST", chroma_host or "chroma")
        chroma_port = int(os.getenv("CHROMA_PORT", chroma_port or 8000))
        
        print(f"[TieredMemory] Hafıza sistemi başlatılıyor (Redis: {redis_host}, Chroma: {chroma_host})...")

        # ── Kısa Süreli: Redis ────────────────────────────────────
        self._redis = None
        if _REDIS_AVAILABLE:
            try:
                self._redis = redis.Redis(
                    host=redis_host, port=redis_port,
                    password=os.getenv("REDIS_PASSWORD"),
                    db=0, decode_responses=True,
                    socket_connect_timeout=3,
                )
                self._redis.ping()
                print(f"[TieredMemory] ✅ Redis bağlantısı OK ({redis_host}:{redis_port})")
            except Exception as exc:
                print(f"[TieredMemory] ⚠️  Redis bağlanamadı: {exc} — kısa süreli hafıza devre dışı.")
                self._redis = None
        else:
            print("[TieredMemory] ⚠️  redis paketi yüklü değil — 'pip install redis'")

        # -- Uzun Sureli: ChromaDB (direkt HTTP) ----------------------
        self._chroma_url = f"http://{chroma_host}:{chroma_port}"
        self._collection_name = collection_name
        self._collection = None
        try:
            resp = _requests.get(f"{self._chroma_url}/api/v1/heartbeat", timeout=3)
            resp.raise_for_status()
            # Koleksiyonu olustur veya ac
            col_resp = _requests.post(
                f"{self._chroma_url}/api/v1/collections",
                json={"name": collection_name, "get_or_create": True},
                timeout=5
            )
            if col_resp.status_code in (200, 201):
                self._collection = col_resp.json().get("id", collection_name)
                print(f"[TieredMemory] \u2705 ChromaDB OK — koleksiyon: '{collection_name}' ({self._chroma_url})")
            else:
                print(f"[TieredMemory] \u26a0\ufe0f ChromaDB koleksiyon hatasi: {col_resp.status_code} {col_resp.text[:80]}")
        except Exception as exc:
            print(f"[TieredMemory] \u26a0\ufe0f ChromaDB baglanamadi: {exc}")
            self._collection = None

    # ─────────────────────────────────────────────────────────────
    # YAZMA
    # ─────────────────────────────────────────────────────────────
    def add_memory(
        self,
        memory_text: str,
        metadata: dict = None,
        tier: str = "short",
    ):
        """
        tier='short'  → Redis (TTL ile geçici)
        tier='long'   → ChromaDB (kalıcı vektörel)
        """
        metadata = metadata or {}
        metadata["timestamp"] = str(time.time())

        if tier == "short":
            self._add_short(memory_text, metadata)
        elif tier == "long":
            self._add_long(memory_text, metadata)
        else:
            print(f"[TieredMemory] Bilinmeyen tier: '{tier}'. 'short' veya 'long' kullanın.")

    def _add_short(self, text: str, metadata: dict):
        if not self._redis:
            print("[TieredMemory:Short] Redis yok — bellek kaydedilemedi.")
            return
        key = f"mem:short:{uuid.uuid4().hex}"
        payload = json.dumps({"text": text, "metadata": metadata}, ensure_ascii=False)
        self._redis.setex(key, SHORT_TERM_TTL, payload)
        count = len(self._redis.keys("mem:short:*"))
        print(f"[TieredMemory:Short] ✅ Redis'e kaydedildi (TTL {SHORT_TERM_TTL}s) | Toplam: {count}")
        if count >= SHORT_TERM_THRESHOLD:
            print(f"[TieredMemory:Short] ⚠️  Eşik aşıldı ({count}/{SHORT_TERM_THRESHOLD}) — distillation öneriliyor.")

    def _add_long(self, text: str, metadata: dict):
        if not self._collection:
            print("[TieredMemory:Long] ChromaDB yok — veri kaydedilemedi.")
            return
        self._collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[str(uuid.uuid4())],
        )
        print(f"[TieredMemory:Long] ✅ ChromaDB'ye kaydedildi: {text[:50]}...")

    # ─────────────────────────────────────────────────────────────
    # ARAMA  (ZOM: Yeni görev öncesi geçmişe bak!)
    # ─────────────────────────────────────────────────────────────
    def search_memory(self, query: str, n_results: int = 3) -> dict:
        """
        Hem kısa hem uzun süreli hafızada arama yapar.
        Döndürdüğü sonuçlar ajan tarafından bağlam olarak kullanılabilir.
        """
        print(f"[TieredMemory] 🔍 Aranan: '{query}'")
        results = {"short_term": [], "long_term": []}

        # ── Kısa süreli arama (Redis — basit string eşleşme) ──────
        if self._redis:
            keys = self._redis.keys("mem:short:*")
            for key in keys[:100]:  # Maksimum 100 key tara
                raw = self._redis.get(key)
                if raw:
                    entry = json.loads(raw)
                    if query.lower() in entry["text"].lower():
                        results["short_term"].append(entry)

        # ── Uzun süreli arama (ChromaDB — vektörel benzerlik) ────
        if self._collection:
            try:
                db_res = self._collection.query(
                    query_texts=[query],
                    n_results=n_results,
                )
                results["long_term"] = db_res
            except Exception as exc:
                print(f"[TieredMemory:Long] Arama hatası: {exc}")

        short_count = len(results["short_term"])
        long_count = len(results["long_term"].get("documents", [[]])[0]) if results["long_term"] else 0
        print(f"[TieredMemory] Bulunan — Kısa: {short_count} | Uzun: {long_count}")
        return results

    def recall_for_task(self, task_description: str) -> str:
        """
        Yeni bir göreve başlamadan önce geçmiş deneyimleri özetle döndürür.
        ZOM: Aynı hatayı tekrar yapma!
        """
        results = self.search_memory(task_description)
        long_docs = results.get("long_term", {}).get("documents", [[]])[0]
        if long_docs:
            summary = "\n".join(f"- {doc}" for doc in long_docs)
            return f"[Geçmiş Deneyimler]\n{summary}"
        return ""

