import json
import os
import sys
import subprocess
import time

# Proje köküne path ekle
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.mq_client import MQClient

class JarvisNotifier:
    """
    ZOM sonuçlarını OpenJarvis'e (sesli veya yazılı bildirim olarak) iletir.
    """
    def __init__(self):
        print("[JarvisNotifier] ZOM -> Jarvis Geri Bildirim Hattı başlatılıyor...")
        self.mq = MQClient()
        self.openjarvis_root = os.getenv("OPENJARVIS_ROOT", "C:/Users/Zezelabs2/OpenJarvis")

    def notify_jarvis(self, message: str):
        """OpenJarvis CLI üzerinden kullanıcıya mesaj atar."""
        try:
            print(f"[JarvisNotifier] 📣 Jarvis'e iletiliyor: {message[:50]}...")
            
            # Jarvis'in chat sistemine mesaj gönder
            # --silent bayrağı varsa sadece loglara düşer, yoksa bildirim tetikleyebilir
            subprocess.run(
                ["uv", "run", "python", "-m", "openjarvis.cli", "chat", "--message", f"[ZOM SİSTEMİ]: {message}"],
                cwd=self.openjarvis_root,
                capture_output=True, text=True, timeout=30
            )
        except Exception as e:
            print(f"[JarvisNotifier] ❗ Bildirim hatası: {e}")

    def process_message(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            msg_type = data.get("type", "notification")
            content = data.get("task", data.get("error", "Bilinmeyen mesaj"))
            agent = data.get("agent", "ZOM")
            
            # Formatlı mesaj
            formatted_msg = f"*{agent}* raporu:\n{content}"
            
            self.notify_jarvis(formatted_msg)
            
        except Exception as e:
            print(f"[JarvisNotifier] Hata: {e}")

    def start(self):
        self.mq.connect()
        # Hem telegram kuyruğunu hem de genel telemetry'yi dinleyebiliriz
        # Şimdilik telegram_out_queue en temiz raporları içeriyor
        self.mq.consume("telegram_out_queue", self.process_message)

if __name__ == "__main__":
    agent = JarvisNotifier()
    agent.start()
