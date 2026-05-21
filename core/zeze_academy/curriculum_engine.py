from typing import Optional
from core.zeze_academy.trace_logger import TraceLogger

class CurriculumEngine:
    def __init__(self):
        self.logger = TraceLogger()

    def analyze_failures(self, tenant_id: str, agent_id: Optional[str] = None) -> list:
        traces = self.logger.get_traces(tenant_id, agent_id)
        return [t for t in traces if not t["success"]]

    def generate_lesson_plan(self, tenant_id: str, agent_id: Optional[str] = None) -> dict:
        failures = self.analyze_failures(tenant_id, agent_id)
        return {
            "lesson_plan": f"Train on {len(failures)} failures.",
            "topics": list(set(t["signature"] for t in failures))
        }

    def recommend_prompt_mutation(self, tenant_id: str, agent_id: Optional[str] = None) -> dict:
        return {
            "recommended_prompt": "Updated instruction based on traces.",
            "approval_required": True
        }
