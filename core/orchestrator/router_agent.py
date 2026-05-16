import os
import json
import logging
import uuid
from typing import Dict, Any, Optional

# CLAUDE CODE PROTOCOL - CORE ROUTER
class RouterAgent:
    """
    Master Orchestrator inspired by Claude Code.
    Routes tasks to specialized ZOM agents (zeze_*) with strict retry logic.
    """
    def __init__(self, mq_client):
        self.mq = mq_client
        self.max_retries = 3
        self.logger = logging.getLogger("zom.router")

    async def route_task(self, task_description: str, context: Dict[str, Any]):
        """
        Analyzes the task and dispatches to the correct queue.
        """
        self.logger.info(f"Routing task: {task_description[:50]}...")
        
        # 1. ANALYZE (Thinking Step)
        agent_type = self._determine_agent(task_description)
        task_id = str(uuid.uuid4())
        
        payload = {
            "task_id": task_id,
            "description": task_description,
            "context": context,
            "retry_count": 0,
            "max_retries": self.max_retries
        }

        # 2. DISPATCH (Action Step)
        queue_name = f"zeze_{agent_type}_queue"
        success = await self.mq.publish(queue_name, payload)
        
        if not success:
            await self._handle_failure(payload, "MQ_PUBLISH_FAILED")
            return {"status": "error", "message": "Failed to dispatch task to queue."}

        return {"status": "dispatched", "task_id": task_id, "agent": agent_type}

    def _determine_agent(self, description: str) -> str:
        # Simple heuristic for now, will be upgraded to LLM-based routing
        desc = description.lower()
        if any(w in desc for w in ["kod", "yaz", "fix", "bug", "git"]): return "eng"
        if any(w in desc for w in ["video", "resim", "tasarım", "medya"]): return "media"
        if any(w in desc for w in ["eğitim", "öğren", "akademi"]): return "academy"
        return "general"

    async def _handle_failure(self, payload: Dict[str, Any], error_type: str):
        """
        Claude Code Style DLQ (Dead Letter Queue) handling.
        Prevents infinite loops by shunting failed tasks to a manual review queue.
        """
        self.logger.error(f"Task {payload['task_id']} failed with {error_type}. Moving to DLQ.")
        await self.mq.publish("zom_dead_letter_queue", {**payload, "error": error_type})
