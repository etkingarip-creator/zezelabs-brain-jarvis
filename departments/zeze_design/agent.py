import os
import uuid
import json
from typing import Dict, Any, Optional
from core.operator_runtime.contracts import AgentResult
from core.operator_runtime.policy_engine import PolicyEngine
from core.zeze_guard.roi_tracker import ROITracker
from core.zeze_guard.anti_loop import AntiLoopEngine
from core.zeze_guard.shadow_ceo_alerts import ShadowCEOAlertClient
from core.ai.providers.visual_director import VisualDirector
from core.ai.providers.parametric_sculptor import ParametricSculptor
from core.ai.providers.layout_composer import LayoutComposer

class ZezeDesignAgent:
    def __init__(self, workspace_root: str = "."):
        self.department = "zeze_design"
        self.workspace_root = workspace_root
        self.visual_director = VisualDirector()
        self.parametric_sculptor = ParametricSculptor()
        self.layout_composer = LayoutComposer()
        self.policy = PolicyEngine()
        self.roi = ROITracker()
        self.anti_loop = AntiLoopEngine()
        self.alerts = ShadowCEOAlertClient()

    def _execute_task(self, goal: str, task_type: str, task_id: Optional[str], output_files: dict) -> AgentResult:
        if not task_id:
            task_id = str(uuid.uuid4())
            
        # Record cost simulation
        self.roi.record_cost(f"{self.department}_agent", task_id, "deepseek-coder", 1400, 450, 0.18)
        
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
        state_dir = os.path.join(self.workspace_root, "zeze_design", "design_reports", task_id)
        os.makedirs(state_dir, exist_ok=True)
        
        # Verify Policy Restrictions
        can_git = self.policy.can_push_git().allowed
        can_deploy = self.policy.can_deploy().allowed
        can_live_trade = self.policy.can_trade_live().allowed
        
        # Write reports
        created_paths = []
        for filename, content in output_files.items():
            path = os.path.join(state_dir, filename)
            with open(path, "w", encoding="utf-8") as f:
                if filename.endswith(".json"):
                     json.dump(content, f, indent=2)
                else:
                     f.write(content)
            created_paths.append(path)
            
        # Record outcome
        self.roi.record_outcome(f"{self.department}_agent", task_id, "task", True)
        
        return AgentResult(
            task_id=task_id,
            success=True,
            department=self.department,
            tool_results=[{
                "task_id": task_id,
                "type": task_type,
                "files_created": created_paths,
                "policy_checks": {
                    "git_push_denied": not can_git,
                    "deploy_denied": not can_deploy,
                    "live_trade_denied": not can_live_trade
                }
            }],
            error=None
        )

    async def run_visual_generation(self, goal: str, task_id: Optional[str] = None) -> AgentResult:
        aesthetic = await self.visual_director.analyze(goal)
        files = {
            "aesthetic_report.md": f"# Visual Director Aesthetic Report\nGoal: {goal}\nStatus: Completed",
            "aesthetic_plan.json": aesthetic
        }
        return self._execute_task(goal, "visual_generation", task_id, files)

    async def run_parametric_design(self, goal: str, specs: dict, task_id: Optional[str] = None) -> AgentResult:
        sculpted = await self.parametric_sculptor.sculpt(specs)
        files = {
            "parametric_report.md": f"# Parametric Sculptor Report\nGoal: {goal}\nStatus: Completed",
            "parametric_specs.json": sculpted
        }
        return self._execute_task(goal, "parametric_design", task_id, files)

    async def run_layout_composition(self, goal: str, layout_specs: dict, task_id: Optional[str] = None) -> AgentResult:
        layout = await self.layout_composer.compose(layout_specs)
        files = {
            "layout_report.md": f"# Layout Composer Report\nGoal: {goal}\nStatus: Completed",
            "composed_layout.json": layout
        }
        return self._execute_task(goal, "layout_composition", task_id, files)

    async def run_n8n_integration(self, goal: str, task_id: Optional[str] = None) -> AgentResult:
        files = {
            "n8n_integration_report.md": f"# n8n Integration Report\nGoal: {goal}\nStatus: Completed",
            "n8n_workflow.json": {"nodes": [], "connections": {}, "active": True}
        }
        return self._execute_task(goal, "n8n_integration", task_id, files)

    async def run_cycle(self) -> Dict[str, Any]:
        """
        Run the complete design pipeline: Visual Director -> Parameter Sculptor -> Layout Composer.
        """
        aesthetic = await self.visual_director.analyze("premium brand identity")
        sculpted = await self.parametric_sculptor.sculpt({"ratio": "3:1", "margin": 0.20})
        composed = await self.layout_composer.compose(sculpted)
        return {
            "aesthetic": aesthetic,
            "parametric": sculpted,
            "layout": composed
        }
