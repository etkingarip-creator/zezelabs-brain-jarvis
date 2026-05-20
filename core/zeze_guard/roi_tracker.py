from typing import Dict, Any, Optional
from core.zeze_guard.storage import get_storage

class ROITracker:
    def __init__(self):
        self.storage = get_storage()

    def record_cost(self, agent_id: str, task_id: str, model: str, tokens_in: int, tokens_out: int, estimated_cost_usd: float):
        self.storage.costs.append({
            "agent_id": agent_id,
            "task_id": task_id,
            "model": model,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "estimated_cost_usd": estimated_cost_usd
        })

    def record_outcome(self, agent_id: str, task_id: str, outcome_type: str, success: bool, metadata: Optional[Dict] = None):
        self.storage.outcomes.append({
            "agent_id": agent_id,
            "task_id": task_id,
            "outcome_type": outcome_type,
            "success": success,
            "metadata": metadata or {}
        })

    def _calculate_base_metrics(self, agent_id: Optional[str] = None, department: Optional[str] = None) -> Dict[str, Any]:
        costs = self.storage.costs
        outcomes = self.storage.outcomes

        if agent_id:
            costs = [c for c in costs if c["agent_id"] == agent_id]
            outcomes = [o for o in outcomes if o["agent_id"] == agent_id]
        
        # If we had a robust department mapping, we'd filter by department here.
        # For MVP, assume agent_id implies department or just aggregate everything if neither provided.

        total_cost_usd = sum(c["estimated_cost_usd"] for c in costs)
        successful_tasks = sum(1 for o in outcomes if o["outcome_type"] == "task" and o["success"])
        failed_tasks = sum(1 for o in outcomes if o["outcome_type"] == "task" and not o["success"])
        successful_commits = sum(1 for o in outcomes if o["outcome_type"] == "commit" and o["success"])
        bugs_fixed = sum(1 for o in outcomes if o["outcome_type"] == "bug_fix" and o["success"])
        docs_generated = sum(1 for o in outcomes if o["outcome_type"] == "docs" and o["success"])
        loop_waste_cost = sum(c["estimated_cost_usd"] for c in costs if "loop" in c.get("model", "").lower()) # naive mock

        cost_per_successful_task = (total_cost_usd / successful_tasks) if successful_tasks > 0 else 0.0
        roi_score = (successful_tasks * 10 + successful_commits * 5 + bugs_fixed * 15 + docs_generated * 2) - total_cost_usd

        return {
            "total_cost_usd": total_cost_usd,
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "successful_commits": successful_commits,
            "bugs_fixed": bugs_fixed,
            "docs_generated": docs_generated,
            "loop_waste_cost": loop_waste_cost,
            "cost_per_successful_task": cost_per_successful_task,
            "roi_score": roi_score
        }

    def agent_score(self, agent_id: str) -> Dict[str, Any]:
        return self._calculate_base_metrics(agent_id=agent_id)

    def department_score(self, department: str) -> Dict[str, Any]:
        # Mock mapping for MVP: all agents with the department in their name or just filter generically.
        # Here we just use a generic call for MVP purposes.
        return self._calculate_base_metrics()
