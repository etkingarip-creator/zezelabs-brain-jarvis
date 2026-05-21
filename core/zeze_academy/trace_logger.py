import json
from typing import Optional
from core.zeze_academy.storage import get_academy_storage
from core.zeze_academy.tenant_policy import TenantPolicy

class TraceLogger:
    def __init__(self):
        self.storage = get_academy_storage()
        self.policy = TenantPolicy()

    def record_trace(self, tenant_id: str, agent_id: str, task_id: str, step_type: str, success: bool, signature: str, metadata: Optional[dict] = None):
        self.policy.assert_tenant_id(tenant_id)
        if not agent_id:
            raise ValueError("agent_id is required")
        if not task_id:
            raise ValueError("task_id is required")

        safe_sig = self.policy.redact_secrets(signature)
        safe_meta = {}
        if metadata:
            for k, v in metadata.items():
                safe_meta[k] = self.policy.redact_secrets(str(v)) if isinstance(v, str) else v

        trace = {
            "tenant_id": tenant_id,
            "agent_id": agent_id,
            "task_id": task_id,
            "step_type": step_type,
            "success": success,
            "signature": safe_sig,
            "metadata": safe_meta
        }
        self.storage.traces.append(trace)

    def get_traces(self, tenant_id: str, agent_id: Optional[str] = None) -> list:
        self.policy.assert_tenant_id(tenant_id)
        traces = [t for t in self.storage.traces if self.policy.validate_tenant_access(tenant_id, t["tenant_id"])]
        if agent_id:
            traces = [t for t in traces if t["agent_id"] == agent_id]
        return traces

    def export_jsonl(self, tenant_id: str) -> str:
        self.policy.assert_tenant_id(tenant_id)
        traces = self.get_traces(tenant_id)
        return "\n".join(json.dumps(t) for t in traces)
