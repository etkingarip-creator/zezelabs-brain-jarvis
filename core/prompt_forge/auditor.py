import os
import json
import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime

from core.mq_client import MQClient
from core.zeze_guard.anti_loop import AntiLoopEngine

log = logging.getLogger("zom.prompt_forge.auditor")

class FailureSignature(BaseModel):
    task_id: str
    agent_id: str
    error_type: str  # e.g. "loop_detected", "path_traversal", "execution_failed", "syntax_error"
    signature: str   # Unique error/signature pattern
    raw_prompt: str = ""
    timestamp: float = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FailureAuditor:
    """
    Katman 1: Auditor Layer (Fast-Parse)
    Gathers and parses telemetry logs, identifying system prompt deviations,
    anti-loop signatures, and policy violations.
    """
    def __init__(self, mq_client: Optional[MQClient] = None):
        self.mq_client = mq_client or MQClient()
        self.anti_loop = AntiLoopEngine()
        self.queue_name = "zom_telemetry_queue"

    async def parse_telemetry(self, telemetry_data: Dict[str, Any]) -> Optional[FailureSignature]:
        """
        Parses live telemetry event and identifies if it matches a failure template.
        """
        try:
            event = telemetry_data.get("event")
            data = telemetry_data.get("data", {})
            task_id = data.get("task_id") or telemetry_data.get("task_id") or "unknown"
            agent_id = data.get("agent_id") or telemetry_data.get("agent_id") or "jarvis_hybrid"
            
            # Check 1: AntiLoopEngine detection
            loop_status = self.anti_loop.detect_loop(agent_id, task_id)
            if loop_status.get("loop_detected"):
                return FailureSignature(
                    task_id=task_id,
                    agent_id=agent_id,
                    error_type="loop_detected",
                    signature=loop_status.get("repeated_signature") or "infinite_loop",
                    raw_prompt=data.get("prompt") or "",
                    metadata={"loop_status": loop_status}
                )

            # Check 2: Path traversal errors or explicit execution failures
            error_msg = data.get("error") or ""
            if "path traversal denied" in error_msg.lower():
                return FailureSignature(
                    task_id=task_id,
                    agent_id=agent_id,
                    error_type="path_traversal",
                    signature="path_traversal_denied",
                    raw_prompt=data.get("prompt") or "",
                    metadata={"error": error_msg}
                )

            # Check 3: Standard failure status
            execution_status = data.get("execution_status") or data.get("status")
            if execution_status == "failed" or event == "hermes_telemetry_failure":
                return FailureSignature(
                    task_id=task_id,
                    agent_id=agent_id,
                    error_type="execution_failed",
                    signature=error_msg or "unknown_execution_failure",
                    raw_prompt=data.get("prompt") or "",
                    metadata=data
                )
                
            return None
        except Exception as e:
            log.error(f"Error parsing telemetry data: {e}")
            return None

    def fetch_fallback_failures(self) -> List[FailureSignature]:
        """
        Scans local file-based fallback queues (from MQClient) for failures.
        This provides a 0-infrastructure fallback if RabbitMQ is offline.
        """
        failures = []
        fallback_queue_dir = os.path.join(self.mq_client.fallback_dir, self.queue_name)
        if not os.path.exists(fallback_queue_dir):
            return failures

        try:
            for filename in os.listdir(fallback_queue_dir):
                if not filename.endswith(".json"):
                    continue
                file_path = os.path.join(fallback_queue_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        telemetry_data = json.load(f)
                    
                    # Run synchronously for file reading
                    import asyncio
                    # Use helper to run coroutine safely if in running loop or run sync
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # We can schedule it, but for simple sync extraction we call a sync variant:
                        sig = self._parse_telemetry_sync(telemetry_data)
                    else:
                        sig = loop.run_until_complete(self.parse_telemetry(telemetry_data))
                        
                    if sig:
                        failures.append(sig)
                except Exception as fe:
                    log.warning(f"Failed to parse file {filename}: {fe}")
        except Exception as e:
            log.error(f"Error scanning fallback queue directory: {e}")
            
        return failures

    def _parse_telemetry_sync(self, telemetry_data: Dict[str, Any]) -> Optional[FailureSignature]:
        """Synchronous helper of parse_telemetry for fallback queue processing."""
        try:
            data = telemetry_data.get("data", {})
            task_id = data.get("task_id") or telemetry_data.get("task_id") or "unknown"
            agent_id = data.get("agent_id") or telemetry_data.get("agent_id") or "jarvis_hybrid"
            
            error_msg = data.get("error") or ""
            if "path traversal denied" in error_msg.lower():
                return FailureSignature(
                    task_id=task_id,
                    agent_id=agent_id,
                    error_type="path_traversal",
                    signature="path_traversal_denied",
                    raw_prompt=data.get("prompt") or "",
                    metadata={"error": error_msg}
                )
                
            execution_status = data.get("execution_status") or data.get("status")
            if execution_status == "failed" or telemetry_data.get("event") == "hermes_telemetry_failure":
                return FailureSignature(
                    task_id=task_id,
                    agent_id=agent_id,
                    error_type="execution_failed",
                    signature=error_msg or "unknown_execution_failure",
                    raw_prompt=data.get("prompt") or "",
                    metadata=data
                )
            return None
        except Exception as e:
            log.error(f"Sync parse telemetry failed: {e}")
            return None
