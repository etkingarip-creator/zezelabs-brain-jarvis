import logging
import json
import os
import sys
from core.mq_client import MQClient
from core.config import config

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger("zeze.fin")

class FinAgent:
    """
    Zeze-Fin Router Agent (v10.0)
    Addresses GÖREV 3.3 - Real-time Financial Routing
    """
    def __init__(self):
        self.mq = MQClient(host=config.RABBITMQ_HOST, user=config.RABBITMQ_USER, password=config.RABBITMQ_PASS)
        self.logger = logger

    def on_task_received(self, ch, method, properties, body):
        try:
            task_data = json.loads(body)
            task_id = task_data.get("task_id", "unknown")
            description = task_data.get("description", "").lower()
            
            self.logger.info(f"📊 Analyzing financial request: {task_id}")

            # SUB-ROUTING LOGIC (GÖREV 3.3)
            if any(w in description for w in ["binance", "buy", "sell", "trade", "işlem"]):
                target = "zeze_binance_queue"
            elif any(w in description for w in ["sinyal", "signal", "indikator", "fiyat"]):
                target = "zeze_signal_queue"
            else:
                target = "zeze_risk_queue"

            self.logger.info(f"🔀 Routing {task_id} to financial sub-unit: {target}")
            self.mq.publish(target, task_data)
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            self.logger.error(f"❌ FinAgent Error: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def start(self):
        if not self.mq.connect(): return
        self.mq.declare_queue("zeze_fin_queue")
        self.logger.info("📊 Zeze-Fin Router is active and listening...")
        self.mq.consume("zeze_fin_queue", self.on_task_received)

if __name__ == "__main__":
    FinAgent().start()
