import logging
import json
import sys
import os
import uuid
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.mq_client import MQClient
from core.config import config

# Setup structured logging placeholder (Actual logging_setup will be created next)
logging.basicConfig(level=config.LOG_LEVEL, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("zom.orchestrator")

class Orchestrator:
    """
    Main ZOM Orchestrator (v10.0)
    Addresses GÖREV 3.1 - Infinite Loop Protection
    """
    def __init__(self):
        self.mq = MQClient(host=config.RABBITMQ_HOST, user=config.RABBITMQ_USER, password=config.RABBITMQ_PASS)
        self.task_retries = {} # {task_id: attempt_count}
        self.logger = logger

    def on_task_received(self, ch, method, properties, body):
        try:
            task_data = json.loads(body)
            task_id = task_data.get("task_id", str(uuid.uuid4()))
            
            # RETRY COUNTER LOGIC (GÖREV 3.1)
            attempt = self.task_retries.get(task_id, 0) + 1
            
            if attempt > config.ZOM_MAX_RETRIES:
                self.logger.error(f"❌ Max retries ({config.ZOM_MAX_RETRIES}) exceeded for task {task_id}.")
                self.mq.publish("failure_reports_queue", {**task_data, "error": "MAX_RETRY_EXCEEDED", "final_attempt": attempt})
                if task_id in self.task_retries: del self.task_retries[task_id]
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            self.task_retries[task_id] = attempt
            task_data["attempt"] = attempt
            
            # ROUTING...
            description = task_data.get("description", "").lower()
            target_queue = self._determine_agent_queue(description)
            
            if self.mq.publish(target_queue, task_data):
                self.logger.info(f"✅ Task {task_id} routed to {target_queue} (Attempt {attempt})")
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        except Exception as e:
            self.logger.exception(f"❌ Orchestrator Error: {e}")
            if "task_data" in locals() and task_data:
                self._shunt_to_dlq(task_data, str(e))
            if ch and method:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def _determine_agent_queue(self, description: str) -> str:
        if any(w in description for w in ["kod", "yaz", "fix", "bug", "git", "dev"]): return "zeze_eng_queue"
        if any(w in description for w in ["video", "resim", "tasarım", "medya"]): return "zeze_media_queue"
        if any(w in description for w in ["eğitim", "öğren", "akademi"]): return "zeze_academy_queue"
        return "zeze_general_queue"

    def _shunt_to_dlq(self, task_data, error):
        logger.warning(f"🚨 Shunting task {task_data.get('task_id')} to DLQ: {error}")
        self.mq.publish("zom_dead_letter_queue", {**task_data, "error": error, "failed_at": datetime.utcnow().isoformat()})

    def start(self):
        if not self.mq.connect():
            logger.error("❌ MQ Connection failed. Orchestrator cannot start.")
            return
        
        queues = [
            "main_orchestrator_queue",
            "zeze_eng_queue",
            "zeze_media_queue",
            "zeze_academy_queue",
            "zom_dead_letter_queue",
        ]

        for q in queues:
            if q != "zom_dead_letter_queue":
                self.mq.setup_dlq(q)
            elif self.mq.channel:
                self.mq.channel.queue_declare(queue=q, durable=True)
        
        logger.info("🚀 ZOM Orchestrator listening on 'main_orchestrator_queue'...")
        self.mq.consume("main_orchestrator_queue", self.on_task_received)

if __name__ == "__main__":
    Orchestrator().start()
