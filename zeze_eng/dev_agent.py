import logging
import json
import os
import sys
import asyncio
from zeze_eng.claw_query_engine import ClawQueryEngine
from core.mq_client import MQClient
from core.config import config

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger("zeze.eng.dev")

class DevAgent:
    """
    Zeze-Eng Dev Agent (v10.0)
    Addresses GÖREV 4.2 - Claw Forge Integration
    """
    def __init__(self):
        self.mq = MQClient(host=config.RABBITMQ_HOST, user=config.RABBITMQ_USER, password=config.RABBITMQ_PASS)
        self.forge = ClawQueryEngine()
        self.logger = logger

    async def handle_task(self, task_data):
        description = task_data.get("description", "")
        task_id = task_data.get("task_id", "unknown")
        
        self.logger.info(f"🛠️ Dev task {task_id} initiated through Claw Forge...")

        # CLAW FORGE EXECUTION (GÖREV 4.2)
        result = await self.forge.execute(description)
        
        # Dispatch to reviewer
        review_payload = {
            **task_data,
            "status": "ready_for_review",
            "forge_result": result,
            "workspace_path": self.forge.workspace
        }
        self.mq.publish("reviewer_queue", review_payload)
        self.logger.info(f"📮 Task {task_id} results sent to reviewer.")

    def on_task_received(self, ch, method, properties, body):
        task_data = json.loads(body)
        asyncio.run(self.handle_task(task_data))
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def start(self):
        if not self.mq.connect(): return
        self.mq.declare_queue("zeze_eng_queue")
        self.logger.info("🛠️ Zeze-Eng DevAgent (CLAW ENABLED) listening...")
        self.mq.consume("zeze_eng_queue", self.on_task_received)

if __name__ == "__main__":
    DevAgent().start()
