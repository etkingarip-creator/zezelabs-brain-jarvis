import os
import json
import logging
from typing import Dict, Any
from datetime import datetime
from core.operator_runtime.base_agent import BaseDepartmentAgent

class ZezeAcademyAgent(BaseDepartmentAgent):
    department = "zeze_academy"

    def __init__(self, workspace_root: str = "."):
        super().__init__(workspace_root=workspace_root)
        self.workspace_root = os.path.realpath(os.path.abspath(workspace_root))

    async def run_cycle(self) -> Dict[str, Any]:
        """Periodic self-execution: Scans and trains poor performers."""
        self.logger.info("Academy running continuous evaluation cycle...")
        
        try:
            from core.zeze_guard.roi_tracker import ROITracker
            tracker = ROITracker()
            
            trained_depts = []
            
            from core.registry.department_profile import DEFAULT_DEPARTMENTS
            for name in DEFAULT_DEPARTMENTS.keys():
                if name == self.department:
                    continue
                
                score_data = tracker.department_score(name)
                roi = score_data.get("roi_score", 0.0)
                failed = score_data.get("failed_tasks", 0)
                
                # If there are failures or ROI is low, compile training curriculum
                if failed > 0 or roi < 10.0:
                    await self._compile_and_save_curriculum(name, score_data)
                    trained_depts.append(name)
                    
            return {
                "status": "completed",
                "trained_departments": trained_depts,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Academy cycle failed: {e}")
            return {"status": "error", "error": str(e)}

    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        # Görev-tipi kapsama: alan içi → uzman handler; tanınmazsa generic (needs_review)
        routes = [(["eğitim", "akademi", "müfredat", "kurs", "öğren", "training", "curriculum", "ders", "öğretim"], self._handle_primary)]
        return await self.dispatch_by_task_type(task_data, routes, 'Sen ZezeLabs Akademi ajanısın. Eğitim müfredatı ve öğrenme içeriği üretirsin.')

    async def _handle_primary(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        from core.observability.tracer import Trace
        task_id = self._safe_task_id(task_data)
        description = task_data.get("description", "Detaylı analiz yap.")
        action = task_data.get("action", "general")
        
        self.logger.info(f"[{task_id}] Görev alındı: {description[:50]}...")
        trace = Trace(department=self.department, task_description=description)
        
        state_dir = os.path.join(self.workspace_root, "departments", self.department, "reports", task_id)
        os.makedirs(state_dir, exist_ok=True)
        report_path = os.path.join(state_dir, "report.json")
        
        if action == "eval_and_train":
            target_dept = task_data.get("target_department")
            if not target_dept:
                trace.finish(status="failed", error="target_department parameter is required")
                return {"success": False, "error": "target_department parameter is required for eval_and_train"}
                
            try:
                from core.zeze_guard.roi_tracker import ROITracker
                tracker = ROITracker()
                score_data = tracker.department_score(target_dept)
                
                curriculum_id = await self._compile_and_save_curriculum(target_dept, score_data)
                output_text = f"Successfully compiled and saved training curriculum {curriculum_id} for {target_dept} in SharedKnowledgeBase."
                
                report_data = {
                    "task_id": task_id,
                    "department": self.department,
                    "timestamp": datetime.now().isoformat(),
                    "query": description,
                    "action": action,
                    "target_department": target_dept,
                    "curriculum_id": curriculum_id,
                    "output": output_text,
                    "status": "completed",
                    "trace_id": trace.trace_id
                }
                with open(report_path, "w", encoding="utf-8") as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False)
                    
                trace.finish(status="success")
                return {
                    "success": True,
                    "report_path": report_path,
                    "task_id": task_id,
                    "trace_id": trace.trace_id,
                    "output": output_text,
                    "target_department": target_dept,
                    "curriculum_id": curriculum_id,
                    "artifacts": [report_path],
                    "deliverable": True,
                }
            except Exception as e:
                trace.finish(status="failed", error=str(e))
                return {"success": False, "error": str(e)}
                
        # Fallback to general AI assistance using LLM
        prompt = f"Academy Task: {description}"
        system_prompt = "Sen ZezeLabs Sürekli Eğitim ve Kesintisiz Gelişim (Academy) ajanısın. Holding ajanlarının performansını artırmak için müfredat hazırlar ve eğitim taktikleri verirsin."
        llm_response = await self.ask_llm(prompt, system_prompt)
        
        trace.estimate_tokens(prompt + llm_response)
        
        report_data = {
            "task_id": task_id,
            "department": self.department,
            "timestamp": datetime.now().isoformat(),
            "query": description,
            "action": action,
            "output": llm_response,
            "status": "completed",
            "trace_id": trace.trace_id
        }
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
            
        trace.finish(status="success")
        return {
            "success": True,
            "report_path": report_path,
            "task_id": task_id,
            "trace_id": trace.trace_id,
            "output": llm_response
        }

    async def _compile_and_save_curriculum(self, target_dept: str, score_data: Dict[str, Any]) -> str:
        """Compiles training guidelines and registers them in the SharedKnowledgeBase."""
        failures = score_data.get("failed_tasks", 0)
        roi = score_data.get("roi_score", 0.0)
        
        # Determine book search query based on target department
        dept_queries = {
            "crypto_trading": "python",
            "app_factory": "react",
            "zeze_design": "html css",
            "zeze_sec": "security",
            "zeze_dev": "git"
        }
        search_query = dept_queries.get(target_dept, "programming")
        
        # Search for free programming books dynamically
        books_recommendation = ""
        try:
            from core.skills.search_free_books import SearchFreeBooksSkill
            search_skill = SearchFreeBooksSkill()
            books_recommendation = await search_skill.execute(query=search_query, limit=3)
        except Exception as e:
            self.logger.error(f"Failed to query free books for curriculum: {e}")
            books_recommendation = f"Failed to retrieve learning resources: {e}"

        training_content = (
            f"CURRICULUM FOR DEPARTMENT: {target_dept.upper()}\n"
            f"Generated At: {datetime.now().isoformat()}\n"
            f"Performance Metrics analyzed: ROI={roi}, Failed Tasks={failures}\n\n"
            f"TRAINING INSTRUCTIONS:\n"
            f"1. To improve success rates, verify key arguments and perform validations before code writes or external requests.\n"
            f"2. Use structured step-by-step thinking for decisions to avoid logical loop waste cost.\n"
            f"3. Refer to holding best practices in SharedKnowledgeBase when encountering ambiguous tasks.\n"
            f"4. If API connections fail, log the detailed error trace and immediately alert the Shadow CEO.\n\n"
            f"RECOMMENDED LEARNING RESOURCES:\n"
            f"{books_recommendation}"
        )
        
        # Save to SharedKnowledgeBase
        from core.knowledge.shared_knowledge import shared_knowledge_base, KnowledgeItem, KnowledgeType
        item = KnowledgeItem(
            id="",
            type=KnowledgeType.BEST_PRACTICE,
            title=f"Academy Custom Refinement and Curriculum for {target_dept.upper()}",
            content=training_content,
            source_department=self.department,
            tags=[target_dept, "curriculum", "training", "refinement"],
            confidence=1.0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        curriculum_id = await shared_knowledge_base.add_knowledge(item)
        self.logger.info(f"Academy registered training curriculum {curriculum_id} for {target_dept}")
        return curriculum_id
