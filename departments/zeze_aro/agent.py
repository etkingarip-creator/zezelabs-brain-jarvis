import os
import uuid
import json
from typing import Dict, Any, Optional
from core.operator_runtime.contracts import AgentResult
from core.operator_runtime.adapters.clawde_process_adapter import ClawdeProcessAdapter
from core.operator_runtime.policy_engine import PolicyEngine
from core.zeze_guard.roi_tracker import ROITracker
from core.zeze_guard.anti_loop import AntiLoopEngine
from core.zeze_guard.shadow_ceo_alerts import ShadowCEOAlertClient

class ZezeAroAgent:
    def __init__(self, workspace_root: str = "."):
        self.department = "zeze_aro"
        self.workspace_root = workspace_root
        self.adapter = ClawdeProcessAdapter(clawde_root=".", workspace_root=self.workspace_root)
        self.policy = PolicyEngine()
        self.roi = ROITracker()
        self.anti_loop = AntiLoopEngine()
        self.alerts = ShadowCEOAlertClient()

    def _execute_task(self, goal: str, task_type: str, task_id: Optional[str] = None) -> AgentResult:
        if not task_id:
            task_id = str(uuid.uuid4())
            
        # Simulate cost
        self.roi.record_cost(f"{self.department}_agent", task_id, "deepseek-coder", 1500, 500, 0.20)
        
        # Simulate Loop detection
        signature = f"cmd_{task_type}_process"
        self.anti_loop.record_event(f"{self.department}_agent", task_id, "command", signature)
        
        loop_check = self.anti_loop.detect_loop(f"{self.department}_agent", task_id)
        if loop_check["loop_detected"]:
            self.alerts.send_alert(
                f"Loop Detected in {self.department}",
                f"Task {task_id} is stuck. Reason: {loop_check['reason']}",
                severity="critical"
            )

        # Output paths
        state_dir = os.path.join(self.workspace_root, "zeze_aro", "dogfood_reports")
        os.makedirs(state_dir, exist_ok=True)
        
        # Verify Policy Restrictions
        can_git = self.policy.can_push_git().allowed
        can_deploy = self.policy.can_deploy().allowed
        can_live_trade = self.policy.can_trade_live().allowed
        
        # Write reports
        report_path = os.path.join(state_dir, f"{task_type}_report.md")
        json_path = os.path.join(state_dir, f"{task_type}_report.json")
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# {task_type.capitalize()} Report\nGoal: {goal}\nStatus: DRY-RUN")
            
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "task_id": task_id,
                "goal": goal,
                "type": task_type,
                "status": "success"
            }, f)
            
        # Record outcome
        self.roi.record_outcome(f"{self.department}_agent", task_id, "task", True)
        
        return AgentResult(
            task_id=task_id,
            success=True,
            department=self.department,
            tool_results=[{
                "task_id": task_id,
                "type": task_type,
                "files_created": [report_path, json_path],
                "policy_checks": {
                    "git_push_denied": not can_git,
                    "deploy_denied": not can_deploy,
                    "live_trade_denied": not can_live_trade
                }
            }],
            error=None
        )

    def run_sales_task(self, goal: str, task_id: Optional[str] = None) -> AgentResult:
        return self._execute_task(goal, "sales", task_id)

    def run_marketing_task(self, goal: str, task_id: Optional[str] = None) -> AgentResult:
        return self._execute_task(goal, "marketing", task_id)

    def run_crm_task(self, goal: str, task_id: Optional[str] = None) -> AgentResult:
        return self._execute_task(goal, "crm", task_id)
