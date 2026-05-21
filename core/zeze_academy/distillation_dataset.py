import json
from typing import Optional
from core.zeze_academy.storage import get_academy_storage
from core.zeze_academy.tenant_policy import TenantPolicy

class DistillationDatasetBuilder:
    def __init__(self):
        self.storage = get_academy_storage()
        self.policy = TenantPolicy()

    def add_trace_example(self, tenant_id: str, input_prompt: str, successful_output: str, metadata: Optional[dict] = None):
        self.policy.assert_tenant_id(tenant_id)
        safe_prompt = self.policy.redact_secrets(input_prompt)
        safe_output = self.policy.redact_secrets(successful_output)
        
        example = {
            "tenant_id": tenant_id,
            "input": safe_prompt,
            "output": safe_output,
            "metadata": metadata or {}
        }
        self.storage.datasets.append(example)

    def export_dataset_jsonl(self, tenant_id: str) -> str:
        self.policy.assert_tenant_id(tenant_id)
        data = [d for d in self.storage.datasets if self.policy.validate_tenant_access(tenant_id, d["tenant_id"])]
        return "\n".join(json.dumps(d) for d in data)
