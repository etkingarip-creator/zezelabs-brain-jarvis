from typing import Optional
from core.zeze_academy.curriculum_engine import CurriculumEngine

class EducatorAgent:
    def __init__(self):
        self.curriculum = CurriculumEngine()

    def run_nightly_review(self, tenant_id: str, agent_id: Optional[str] = None) -> dict:
        failures = self.curriculum.analyze_failures(tenant_id, agent_id)
        lesson_plan = self.curriculum.generate_lesson_plan(tenant_id, agent_id)
        mutation = self.curriculum.recommend_prompt_mutation(tenant_id, agent_id)
        
        return {
            "status": "success",
            "failures_analyzed": len(failures),
            "lesson_plan": lesson_plan,
            "prompt_mutation": mutation,
            "approval_required": mutation["approval_required"]
        }
