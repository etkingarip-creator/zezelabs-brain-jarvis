import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.mq_client import MQClient

MAX_RETRY = 3

def on_task(ch, method, properties, body):
    task_data = json.loads(body)
    task_id = str(task_data.get("id", "tmp"))
    attempt = int(task_data.get("attempt", 1))
    print(f"[OutreachAgent] Görev #{task_id} (Deneme {attempt}/{MAX_RETRY})")
    
    if attempt > MAX_RETRY: return
    print("[OutreachAgent] Gmail API ile email gönderiliyor...")
    time.sleep(1)
    print(f"[OutreachAgent] ✅ İletişim e-postası gönderildi.")

def main():
    mq = MQClient()
    mq.connect()
    mq.declare_queue("outreach_queue")
    print("[OutreachAgent] Başlatıldı. Bekleniyor...")
    try: mq.consume("outreach_queue", on_task)
    except KeyboardInterrupt: pass

if __name__ == "__main__": main()
