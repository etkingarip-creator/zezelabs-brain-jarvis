import os
import uuid
import json
from typing import Dict, Any, Optional
from core.operator_runtime.contracts import AgentResult
from core.operator_runtime.policy_engine import PolicyEngine
from core.zeze_guard.roi_tracker import ROITracker
from core.zeze_guard.anti_loop import AntiLoopEngine
from core.zeze_guard.shadow_ceo_alerts import ShadowCEOAlertClient
from core.ai.providers.trend_scout import TrendScout
from core.ai.providers.sandbox_engineer import SandboxEngineer
from core.ai.providers.injector import Injector

class ZezeRndAgent:
    def __init__(self, workspace_root: str = "."):
        self.department = "zeze_rnd"
        self.workspace_root = workspace_root
        self.trend_scout = TrendScout()
        self.sandbox_engineer = SandboxEngineer()
        self.injector = Injector()
        self.policy = PolicyEngine()
        self.roi = ROITracker()
        self.anti_loop = AntiLoopEngine()
        self.alerts = ShadowCEOAlertClient()

    def _execute_task(self, goal: str, task_type: str, task_id: Optional[str], output_files: dict) -> AgentResult:
        if not task_id:
            task_id = str(uuid.uuid4())
            
        # Record cost simulation
        self.roi.record_cost(f"{self.department}_agent", task_id, "deepseek-coder", 1800, 600, 0.24)
        
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
        state_dir = os.path.join(self.workspace_root, "zeze_rnd", "research_reports", task_id)
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

    async def run_trend_scan(self, goal: str, task_id: Optional[str] = None) -> AgentResult:
        trends = await self.trend_scout.scan()
        files = {
            "trend_report.md": f"# Trend Scout Report\nGoal: {goal}\nStatus: Completed",
            "trends.json": {"trends": trends}
        }
        return self._execute_task(goal, "web_scan", task_id, files)

    async def run_sandbox_test(self, goal: str, tech: dict, task_id: Optional[str] = None) -> AgentResult:
        test_result = await self.sandbox_engineer.test(tech)
        files = {
            "sandbox_test_report.md": f"# Sandbox Test Report\nGoal: {goal}\nStatus: Completed",
            "test_result.json": test_result
        }
        return self._execute_task(goal, "tech_eval", task_id, files)

    async def run_safe_injection(self, goal: str, tech: dict, task_id: Optional[str] = None) -> AgentResult:
        injection_result = await self.injector.inject(tech)
        files = {
            "injection_report.md": f"# Safe Code Injection Report\nGoal: {goal}\nStatus: Completed",
            "injection_result.json": injection_result
        }
        return self._execute_task(goal, "autonomous_inject", task_id, files)

    async def run_cycle(self) -> Dict[str, Any]:
        """
        Run the complete pipeline: The Scout -> Sandbox Engineer -> Injector.
        """
        # 1. Scan
        trends = await self.trend_scout.scan()
        top_trend = trends[0] if trends else {"title": "Kokoro-TTS", "score": 0.95}
        
        # 2. Test
        test_result = await self.sandbox_engineer.test(top_trend)
        
        # 3. Inject
        injection_result = {}
        if test_result.get("passed", False):
            injection_result = await self.injector.inject(top_trend)
            
        return {
            "trend": top_trend,
            "sandbox": test_result,
            "injection": injection_result
        }
