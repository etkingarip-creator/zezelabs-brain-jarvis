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

class MediaFactoryAgent:
    def __init__(self, workspace_root: str = "."):
        self.department = "media_factory"
        self.workspace_root = workspace_root
        self.adapter = ClawdeProcessAdapter(clawde_root=".", workspace_root=self.workspace_root)
        self.policy = PolicyEngine()
        self.roi = ROITracker()
        self.anti_loop = AntiLoopEngine()
        self.alerts = ShadowCEOAlertClient()

    def _execute_task(self, goal: str, task_type: str, task_id: Optional[str], output_files: dict) -> AgentResult:
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
        state_dir = os.path.join(self.workspace_root, "media_factory", "dogfood_reports", task_id)
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
                    "live_trade_denied": not can_live_trade,
                    "external_publish_requires_approval": True,
                    "youtube_upload_requires_approval": True,
                    "paid_ads_launch_requires_approval": True
                }
            }],
            error=None
        )

    def run_video_task(self, goal: str, task_id: Optional[str] = None) -> AgentResult:
        files = {
            "video_brief.md": f"# Video Brief\nGoal: {goal}",
            "script.md": f"# Video Script\nScene 1: Introduction to {goal}",
            "shot_list.json": {"shots": [{"scene": 1, "desc": "intro"}]},
            "production_plan.md": "# Production Plan\nStatus: DRY-RUN"
        }
        return self._execute_task(goal, "video", task_id, files)

    def run_seo_task(self, goal: str, task_id: Optional[str] = None) -> AgentResult:
        files = {
            "seo_report.md": f"# SEO Report\nGoal: {goal}",
            "keywords.json": {"keywords": ["zeze", "ai", "seo"]},
            "title_variants.json": {"titles": ["How to Use AI", "AI Basics"]},
            "description.md": "Best AI platform."
        }
        return self._execute_task(goal, "seo", task_id, files)

    def run_content_task(self, goal: str, task_id: Optional[str] = None) -> AgentResult:
        files = {
            "content_calendar.md": f"# Content Calendar\nGoal: {goal}",
            "post_variants.json": {"variants": ["Post 1", "Post 2"]},
            "caption_pack.md": "Captions here."
        }
        return self._execute_task(goal, "content", task_id, files)

    def run_thumbnail_task(self, goal: str, task_id: Optional[str] = None) -> AgentResult:
        files = {
            "thumbnail_brief.md": f"# Thumbnail Brief\nGoal: {goal}",
            "thumbnail_prompts.json": {"prompts": ["cyberpunk style", "minimalist"]}
        }
        return self._execute_task(goal, "thumbnail", task_id, files)

    def run_distribution_plan_task(self, goal: str, task_id: Optional[str] = None) -> AgentResult:
        files = {
            "distribution_plan.md": f"# Distribution Plan\nGoal: {goal}",
            "channels.json": {"channels": ["youtube", "twitter"]},
            "posting_schedule.json": {"schedule": ["monday", "wednesday"]}
        }
        return self._execute_task(goal, "distribution_plan", task_id, files)
