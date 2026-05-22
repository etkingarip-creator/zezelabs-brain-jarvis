import logging
import json
import sys
import os
import uuid
import threading
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.mq_client import MQClient
from core.config import config

# Setup structured logging placeholder
logging.basicConfig(level=config.LOG_LEVEL, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("zom.orchestrator")

class Orchestrator:
    """
    Main ZOM Orchestrator (v11.0)
    Addresses GÖREV 3.1 - Infinite Loop Protection & Multi-agent Orchestration
    """
    def __init__(self):
        self.mq = MQClient(host=config.RABBITMQ_HOST, user=config.RABBITMQ_USER, password=config.RABBITMQ_PASS)
        self.task_retries = {} # {task_id: attempt_count}
        self.logger = logger
        self.threads = []

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
            
            # 3-Layer Security Shield
            import asyncio
            from core.security.injection_warden import InjectionWarden
            from core.security.code_healer import CodeHealer
            from core.security.token_sanitizer import TokenSanitizer
            
            description = task_data.get("description", "")
            
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            # Layer 1: Semantic Wall (InjectionWarden)
            warden = InjectionWarden()
            warden_res = loop.run_until_complete(warden.analyze(description))
            if not warden_res.get("safe", True):
                self.logger.warning(f"🚨 Layer 1 Prompt Injection Blocked: {warden_res['threats']}")
                task_data["status"] = "blocked"
                task_data["security_breach"] = "injection_detected"
                task_data["threats"] = warden_res["threats"]
                self._shunt_to_dlq(task_data, "SECURITY_BREACH_INJECTION")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
                
            # Layer 2: Static & Live Wall (CodeHealer)
            healer = CodeHealer()
            healer_res = loop.run_until_complete(healer.analyze(description))
            if not healer_res.get("safe", True):
                self.logger.warning(f"🚨 Layer 2 Code Vuln Auto-Patched: {healer_res['vulnerabilities']}")
                if "patched_code" in healer_res:
                    task_data["description"] = healer_res["patched_code"]
                    description = healer_res["patched_code"]
                    
            # Layer 3: TokenSanitizer (DLP Secret scrubber)
            sanitizer = TokenSanitizer()
            sanitizer_res = loop.run_until_complete(sanitizer.sanitize(description))
            if not sanitizer_res.get("safe", True):
                self.logger.warning(f"🚨 Layer 3 DLP Leak Sanitized: {sanitizer_res['leaks']}")
                if "sanitized" in sanitizer_res:
                    task_data["description"] = sanitizer_res["sanitized"]
                    description = sanitizer_res["sanitized"]
            
            # ROUTING...
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
        desc_lower = description.lower()
        if any(w in desc_lower for w in ["güvenlik", "security", "vuln", "scan", "healer", "warden", "sanitizer", "shield", "sec"]):
            return "zeze_sec_queue"
        if any(w in desc_lower for w in ["kod", "yaz", "fix", "bug", "git", "dev"]): return "zeze_eng_queue"
        if any(w in desc_lower for w in ["video", "resim", "tasarım", "medya"]): return "zeze_media_queue"
        if any(w in desc_lower for w in ["eğitim", "öğren", "akademi"]): return "zeze_academy_queue"
        return "zeze_general_queue"

    def _shunt_to_dlq(self, task_data, error):
        logger.warning(f"🚨 Shunting task {task_data.get('task_id')} to DLQ: {error}")
        self.mq.publish("zom_dead_letter_queue", {**task_data, "error": error, "failed_at": datetime.utcnow().isoformat()})

    def _worker_callback(self, queue_name: str):
        def callback(ch, method, properties, body):
            try:
                task_data = json.loads(body)
                task_id = task_data.get("task_id", "unknown")
                self.logger.info(f"👷 [Worker - {queue_name}] Received task {task_id}: {task_data.get('description', '')}")
                
                # Simulate agent processing
                task_data["status"] = "completed"
                task_data["processed_by"] = f"worker_{queue_name}"
                task_data["completed_at"] = datetime.utcnow().isoformat()
                
                # Acknowledge the message
                ch.basic_ack(delivery_tag=method.delivery_tag)
                self.logger.info(f"👷 [Worker - {queue_name}] Task {task_id} successfully processed and acknowledged.")
            except Exception as e:
                self.logger.error(f"❌ [Worker - {queue_name}] Error processing task: {e}")
                if ch and method:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return callback

    def _start_worker_thread(self, queue_name: str):
        def run():
            thread_mq = MQClient(host=config.RABBITMQ_HOST, user=config.RABBITMQ_USER, password=config.RABBITMQ_PASS)
            # Try to connect, otherwise fall back to local folder polling
            thread_mq.connect()
            try:
                thread_mq.declare_queue(queue_name)
                thread_mq.consume(queue_name, self._worker_callback(queue_name))
            except Exception as e:
                self.logger.error(f"❌ [Worker - {queue_name}] Background thread error: {e}")
            finally:
                thread_mq.close()

        t = threading.Thread(target=run, name=f"worker_{queue_name}", daemon=True)
        t.start()
        self.threads.append(t)
        self.logger.info(f"🧵 Spawned background worker thread for queue: {queue_name}")

    def start(self):
        # Even if connection fails, fallback mode in MQClient enables local execution
        self.mq.connect()
        
        queues = [
            "main_orchestrator_queue",
            "zeze_eng_queue",
            "zeze_media_queue",
            "zeze_academy_queue",
            "zeze_general_queue",
            "zeze_sec_queue",
            "zom_dead_letter_queue",
        ]

        for q in queues:
            if q != "zom_dead_letter_queue":
                self.mq.setup_dlq(q)
            elif self.mq.channel:
                self.mq.channel.queue_declare(queue=q, durable=True)
        
        # Start background worker subscription threads for agent queues
        worker_queues = [
            "zeze_eng_queue",
            "zeze_media_queue",
            "zeze_academy_queue",
            "zeze_general_queue",
            "zeze_sec_queue",
        ]
        for wq in worker_queues:
            self._start_worker_thread(wq)

        logger.info("🚀 ZOM Orchestrator listening on 'main_orchestrator_queue'...")
        self.mq.consume("main_orchestrator_queue", self.on_task_received)

if __name__ == "__main__":
    Orchestrator().start()
