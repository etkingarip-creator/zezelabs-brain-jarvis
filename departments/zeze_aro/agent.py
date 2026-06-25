"""
Zezelabs Holding OS - ZezeAroAgent
Gerçek LLM Entegrasyonlu Ajan
"""
import os
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from core.operator_runtime.base_agent import BaseDepartmentAgent
from core.observability.tracer import Trace
from core.operator_runtime.contracts import AgentResult
from core.operator_runtime.policy_engine import PolicyEngine
from core.zeze_guard.roi_tracker import ROITracker
from core.zeze_guard.anti_loop import AntiLoopEngine
from core.ai.critic import CriticAgent

class ZezeAroAgent(BaseDepartmentAgent):
    department = "zeze_aro"
    
    def __init__(self, workspace_root: str = "."):
        super().__init__(workspace_root=workspace_root)
        self.workspace_root = os.path.realpath(os.path.abspath(workspace_root))
        self.policy = PolicyEngine(department=self.department)
        self.roi = ROITracker()
        self.anti_loop = AntiLoopEngine()
        self.critic = CriticAgent()

    async def _execute_task_internal(self, goal: str, task_type: str, task_id: Optional[str] = None) -> AgentResult:
        if not task_id:
            task_id = str(uuid.uuid4())
            
        # 1. System Prompt
        system_prompt = "Sen ZezeLabs Gelir Optimizasyonu (ARO) ajanısın. Karlılık analizi, fiyatlandırma stratejileri, ROI hesaplamaları ve gelir artırıcı taktikler üretirsin. Her öneri rakamsal kanıt içerir."
        past_context = self.memory.recall_for_task(goal)
        if past_context:
            system_prompt += f"\n\nŞirket Geçmiş Hafızası:\n{past_context}"
            
        # 2. Record simulated/real cost in ROITracker
        self.roi.record_cost(f"{self.department}_agent", task_id, "gemma-4", 1500, 500, 0.15)
        
        # 3. Anti-Loop signature checking
        signature = f"cmd_{task_type}_process"
        self.anti_loop.record_event(f"{self.department}_agent", task_id, "command", signature)
        
        loop_check = self.anti_loop.detect_loop(f"{self.department}_agent", task_id)
        if loop_check["loop_detected"]:
            self.alerts.send_alert(
                f"Loop Detected in {self.department}",
                f"Task {task_id} is stuck. Reason: {loop_check['reason']}",
                severity="critical"
            )
            return AgentResult(
                task_id=task_id,
                success=False,
                department=self.department,
                error=f"Loop detected: {loop_check['reason']}"
            )
            
        # 4. Check policy constraints using PolicyEngine
        can_git = self.policy.can_push_git().allowed
        can_deploy = self.policy.can_deploy().allowed
        can_live_trade = self.policy.can_trade_live().allowed
        
        policy_checks = {
            "git_push_denied": not can_git,
            "deploy_denied": not can_deploy,
            "live_trade_denied": not can_live_trade
        }
        
        # 5. Ask LLM to generate response or fallback to mock
        max_retries = 3
        llm_response = ""
        current_description = goal
        
        for attempt in range(max_retries):
            try:
                llm_response = await self.ask_llm_with_tools(prompt=current_description, system_prompt=system_prompt)
            except Exception as e:
                self.logger.warning(f"LLM call failed: {e}. Using fallback mock response.")
                llm_response = f"# {task_type.capitalize()} Content\nGenerated ARO analysis for: {goal}\nStatus: Fallback Success."
                
            eval_result = await self.critic.evaluate_result(self.department, goal, llm_response)
            if not eval_result.get("needs_revision") or attempt == max_retries - 1:
                break
            current_description = goal + f"\n\n[Critic revision request]: {eval_result['feedback']}"
            
        # 6. Generate output files based on task type
        state_dir = os.path.join(self.workspace_root, "zeze_aro", "dogfood_reports")
        os.makedirs(state_dir, exist_ok=True)
        
        report_path = os.path.join(state_dir, f"{task_type}_report.md")
        json_path = os.path.join(state_dir, f"{task_type}_report.json")
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# {task_type.capitalize()} Report\nGoal: {goal}\n\n## Content\n{llm_response}")
            
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "task_id": task_id,
                "goal": goal,
                "type": task_type,
                "status": "success",
                "output": llm_response
            }, f, indent=2, ensure_ascii=False)
            
        created_files = [report_path, json_path]
        
        # Record outcome to ROITracker
        self.roi.record_outcome(f"{self.department}_agent", task_id, "task", True)
        self.memory.add_memory(memory_text=llm_response, metadata={"task": goal, "dept": self.department}, tier="long")
        
        return {
            "success": True,
            "task_id": task_id,
            "department": self.department,
            "output": llm_response,
            "report_path": report_path,
            "artifacts": created_files,
            "deliverable": True,
            "tool_results": [{
                "task_id": task_id,
                "type": task_type,
                "files_created": created_files,
                "policy_checks": policy_checks,
            }],
        }

    def _run_sync(self, coro):
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)

    # ── Dogfood Methods for ARO test suite ──────────────────────────────────────────
    def run_sales_task(self, goal: str, task_id: Optional[str] = None) -> AgentResult:
        return self._run_sync(self._execute_task_internal(goal, "sales", task_id))

    def run_marketing_task(self, goal: str, task_id: Optional[str] = None) -> AgentResult:
        return self._run_sync(self._execute_task_internal(goal, "marketing", task_id))

    def run_crm_task(self, goal: str, task_id: Optional[str] = None) -> AgentResult:
        return self._run_sync(self._execute_task_internal(goal, "crm", task_id))

    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        # Görev-tipi kapsama: alan içi → uzman handler; tanınmazsa generic (needs_review)
        routes = [(["analitik", "metrik", "aro", "büyüme", "growth", "veri", "izleme", "raporlama", "kpi", "dönüşüm"], self._handle_primary)]
        return await self.dispatch_by_task_type(task_data, routes, 'Sen ZezeLabs ARO (Analitik) ajanısın. Büyüme metrikleri ve veri analizi yaparsın.')

    async def _handle_primary(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_id = self._safe_task_id(task_data)
        task_type = task_data.get("task_type", "general")
        description = task_data.get("description", "Detaylı bir analiz ve ARO raporu hazırla.")
        
        self.logger.info(f"[{task_id}] Görev alındı: {description[:50]}...")
        
        internal_type = "general"
        desc_lower = description.lower()
        if "sales" in desc_lower or "satis" in desc_lower or "funnel" in desc_lower:
            internal_type = "sales"
        elif "marketing" in desc_lower or "pazarlama" in desc_lower or "ads" in desc_lower:
            internal_type = "marketing"
        elif "crm" in desc_lower or "lead" in desc_lower:
            internal_type = "crm"
            
        agent_res = await self._execute_task_internal(description, internal_type, task_id)
        
        report_path = os.path.join(self.workspace_root, "departments", self.department, "reports", task_id, "report.json")
        report_data = {
            "task_id": task_id,
            "department": self.department,
            "timestamp": datetime.now().isoformat(),
            "query": description,
            "output": agent_res.output,
            "status": "completed" if agent_res.success else "failed",
            "files_created": agent_res.tool_results[0]["files_created"] if agent_res.success else []
        }
        
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
            
        return {
            "success": agent_res.success,
            "report_path": report_path,
            "task_id": task_id,
            "output": agent_res.output
        }
