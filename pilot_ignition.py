import os
import sys
import json
import time

# Proje köküne path ekle
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.mq_client import MQClient

def main():
    print("🚀 ZOM v4 IGNITION: PHOENIX LOGIN GÖREVİ BAŞLATILIYOR...")
    mq = MQClient()
    mq.connect()
    
    # Hedef: Orchestrator
    target_queue = "main_orchestrator_queue"
    mq.declare_queue(target_queue)
    
    task_payload = {
        "id": "PHOENIX_001",
        "task": "React kullanarak karanlık temalı (dark mode) ve sadece kullanıcı adı / şifre alanları olan bir 'Phoenix Login' sayfası kodu yaz. Terminal üzerinden bu kodu çalıştırıp test et.",
        "timestamp": time.time()
    }
    
    mq.publish(target_queue, task_payload)
    print(f"✅ Görev {target_queue} kuyruğuna ateşlendi!")
    print(task_payload)

if __name__ == "__main__":
    main()
