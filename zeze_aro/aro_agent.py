import os
import sys
import json
import time

# Proje köküne path ekle
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.mq_client import MQClient

mq: MQClient | None = None

def on_aro_task_received(ch, method, properties, body):
    try:
        task_data = json.loads(body)
        task_description = task_data.get("task", "")
        task_id = str(task_data.get("id", int(time.time())))
        
        print(f"\n{'='*60}")
        print(f"[ARO Agent] Görev #{task_id} alındı: {task_description}")
        print(f"{'='*60}")
        
        # Otonom Kaynak Optimizasyonu ve Performans Analizi
        print("[ARO Agent] Holding kaynakları ve Ajan verimliliği analiz ediliyor...")
        time.sleep(2)
        
        # Simüle edilmiş analiz raporu
        report = (
            f"📊 ARO Optimizasyon Raporu (Görev: {task_id})\n"
            f"- Tahmini Token Maliyeti: 24,500 T\n"
            f"- Ajan Başarı Oranı (AEC): 0.94\n"
            f"- RabbitMQ Verimliliği: %99.9\n"
            f"- Darboğaz Tespiti: YOK"
        )
        print(report)
        
        # Telegram'a raporla
        mq.publish("telegram_queue", {
            "message": f"📈 [ZOM ARO RAPORU]\n\n{report}"
        })
        
        # Görev başarıyla bitti
        print(f"[ARO Agent] Görev #{task_id} tamamlandı.")
        
    except Exception as e:
        print(f"[ARO Agent] Beklenmedik hata: {e}")

def main():
    print("[ARO Agent] Autonomous Resource Optimization departmanı uyandırıldı.")
    global mq
    mq = MQClient()
    mq.connect()
    mq.declare_queue("aro_queue")
    mq.declare_queue("telegram_queue")
    
    try:
        mq.consume("aro_queue", on_aro_task_received)
    except KeyboardInterrupt:
        print("[ARO Agent] Kapatılıyor.")

if __name__ == "__main__":
    main()
