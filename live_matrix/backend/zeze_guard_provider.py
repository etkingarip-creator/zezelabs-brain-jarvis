from datetime import datetime, timezone
from core.zeze_guard.storage import get_storage
from core.zeze_guard.anti_loop import AntiLoopEngine
from core.zeze_guard.roi_tracker import ROITracker

class ZezeGuardProvider:
    def __init__(self):
        self.storage = get_storage()
        self.anti_loop = AntiLoopEngine()
        self.roi = ROITracker()

    def get_zeze_guard_snapshot(self) -> dict:
        anti_loop_data = self.get_loop_alerts()
        roi_data = self.get_roi_summary()
        alerts_data = self.get_shadow_ceo_alerts()
        
        return {
            "anti_loop": anti_loop_data,
            "roi": roi_data,
            "alerts": alerts_data,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

    def get_loop_alerts(self) -> dict:
        # Calculate active loops based on events
        active_loops = 0
        recommendations = []
        
        # Simple scan
        agent_tasks = set((e["agent_id"], e["task_id"]) for e in self.storage.events)
        for agent_id, task_id in agent_tasks:
            res = self.anti_loop.detect_loop(agent_id, task_id)
            if res["loop_detected"]:
                active_loops += 1
                recommendations.append(f"Task {task_id} (Agent {agent_id}): {res['recommendation']}")

        return {
            "active_loops": active_loops,
            "freeze_recommendations": recommendations
        }

    def get_roi_summary(self) -> dict:
        # Calculate overall ROI
        score = self.roi.department_score("all")
        
        # Get unique agents and departments
        agents = list(set(c["agent_id"] for c in self.storage.costs))
        
        return {
            "agents": agents,
            "departments": ["all"],
            "total_cost_usd": score["total_cost_usd"],
            "successful_tasks": score["successful_tasks"],
            "failed_tasks": score["failed_tasks"]
        }

    def get_shadow_ceo_alerts(self) -> list:
        return self.storage.alerts

    def get_queue_freeze_recommendations(self) -> list:
        return self.get_loop_alerts()["freeze_recommendations"]
