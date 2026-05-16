import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.mq_client import MQClient

def on_failure(ch, method, properties, body):
    try:
        data = json.loads(body)
        task_id = data.get("task_id", "UNKNOWN")
        reason = data.get("message", "No reason provided")
        
        print(f"\n🚨 [RED ALARM] Görev Çöktü: {task_id}")
        print(f"🚨 Sebep: {reason}")
        print("🚨 War Room Paneline Kritik Hata Sinyali Gönderiliyor...\n")
        
        # Bu servis ayrıca WebSockets veya başka bir yolla frontend'e push yapabilir.
        # Şimdilik sadece stdout'a basıyor, War Room logları yakalayacak.
        
    except Exception as e:
        print(f"[FailureMonitor] Hata: {e}")

def main():
    mq = MQClient()
    mq.connect()
    mq.declare_queue("failure_reports_queue")
    print("🔴 Failure Monitor aktif. Çöken görevler bekleniyor...")
    try:
        mq.consume("failure_reports_queue", on_failure)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
