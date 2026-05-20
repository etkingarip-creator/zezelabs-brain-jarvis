from typing import Dict, Any, Optional
from core.zeze_guard.storage import get_storage

class AntiLoopEngine:
    def __init__(self):
        self.storage = get_storage()

    def record_event(self, agent_id: str, task_id: str, event_type: str, signature: str, metadata: Optional[Dict] = None):
        self.storage.events.append({
            "agent_id": agent_id,
            "task_id": task_id,
            "event_type": event_type,
            "signature": signature,
            "metadata": metadata or {}
        })

    def detect_loop(self, agent_id: str, task_id: str) -> Dict[str, Any]:
        task_events = [e for e in self.storage.events if e["agent_id"] == agent_id and e["task_id"] == task_id]
        
        signature_counts = {}
        for event in task_events:
            sig = event["signature"]
            signature_counts[sig] = signature_counts.get(sig, 0) + 1

        for sig, count in signature_counts.items():
            if count >= 3:
                return {
                    "loop_detected": True,
                    "reason": f"Signature repeated {count} times",
                    "repeated_signature": sig,
                    "recommendation": "Pause agent task and review logic."
                }

        return {
            "loop_detected": False,
            "reason": "No loop detected",
            "repeated_signature": None,
            "recommendation": "Continue execution."
        }

    def should_freeze_queue(self, agent_id: str, task_id: str) -> bool:
        return self.detect_loop(agent_id, task_id)["loop_detected"]

    def reset_task(self, task_id: str):
        self.storage.events = [e for e in self.storage.events if e["task_id"] != task_id]
