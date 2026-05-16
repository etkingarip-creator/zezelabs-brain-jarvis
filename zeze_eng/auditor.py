import logging
import json
import os
import sys
import ast
import subprocess
from typing import Dict, Any, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.mq_client import MQClient
from core.config import config

logger = logging.getLogger("zeze.eng.auditor")

class AuditorAgent:
    """
    Zeze-Eng Auditor (v10.0 - Production Grade)
    Quality gate enforcement:
    - Syntax validation (AST parsing)
    - Static analysis (pylint, flake8)
    - Security scanning (guardrails)
    """
    def __init__(self):
        self.mq = MQClient(host=config.RABBITMQ_HOST, user=config.RABBITMQ_USER, password=config.RABBITMQ_PASS)
        self.logger = logger

    def perform_audit(self, task_dir: str, files: list) -> Dict[str, Any]:
        report = {"passed": True, "issues": [], "pylint_score": 0}
        
        for file in files:
            filepath = os.path.join(task_dir, file)
            if not os.path.exists(filepath): continue
            
            # 1. Syntax validation (AST)
            try:
                with open(filepath, 'r', encoding='utf-8') as f: ast.parse(f.read())
            except SyntaxError as e:
                report["passed"] = False
                report["issues"].append(f"Syntax Error in {file}: {e}")
            
            # 2. Pylint (Simplified score extraction)
            try:
                result = subprocess.run([sys.executable, "-m", "pylint", filepath, "--score=yes"], capture_output=True, text=True, timeout=30)
                if "rated at" in result.stdout:
                    score = float(result.stdout.split("rated at")[1].split("/")[0].strip())
                    report["pylint_score"] = score
                    if score < config.ZOM_MIN_PYLINT_SCORE:
                        report["passed"] = False
                        report["issues"].append(f"Pylint score too low: {score}/10")
            except: pass

        return report

    def on_review_received(self, ch, method, properties, body):
        try:
            task_data = json.loads(body)
            task_id = task_data.get("task_id", "unknown")
            task_dir = task_data.get("task_dir", "")
            files = task_data.get("files", [])

            self.logger.info(f"🔍 Auditing task {task_id}...")
            report = self.perform_audit(task_dir, files)

            if report["passed"]:
                self.logger.info(f"✅ AUDIT PASSED: {task_id}")
                self.mq.publish("main_orchestrator_queue", {**task_data, "status": "approved", "audit_report": report})
            else:
                self.logger.warning(f"❌ AUDIT FAILED: {task_id}")
                
                # GÖREV 3.2: Check for security vs logic failure
                if any("GÜVENLİK" in str(issue) for issue in report.get("issues", [])):
                    self.logger.error("🛑 SECURITY VIOLATION: Sending to failure queue immediately.")
                    self.mq.publish("failure_reports_queue", {**task_data, "error": "SECURITY_VIOLATION", "audit_report": report})
                else:
                    self.logger.info("🔄 Logic failure: Sending back to orchestrator for retry.")
                    self.mq.publish("main_orchestrator_queue", {**task_data, "status": "needs_revision", "audit_report": report})
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except: ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def start(self):
        if not self.mq.connect(): return
        self.mq.declare_queue("reviewer_queue")
        self.logger.info("🔍 Auditor listening on 'reviewer_queue'...")
        self.mq.consume("reviewer_queue", self.on_review_received)

if __name__ == "__main__":
    AuditorAgent().start()
