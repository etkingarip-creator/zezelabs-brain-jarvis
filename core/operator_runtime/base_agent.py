"""
BaseDepartmentAgent — Ortak departman ajan kontratı.

Önceki sürümde her ajan farklı bir metod adı kullanıyordu (run_dry_task,
run_paper_task, execute_task, run_cycle …). Orchestrator bunları
koordine edemiyordu. Bu sınıf, departmana özgü mantığı koruyarak iki
standart giriş noktası tanımlar:

    • ``run_cycle()``     — periyodik öz-yürütme döngüsü (scout, telemetry).
    • ``execute_task()``  — orchestrator'dan gelen tek bir görevi yürütür.

Telemetry (ROI, AntiLoop, ShadowCEO alerts) burada merkezleştirilir, böylece
her ajan kendi instance'ını yaratmak yerine ortak storage üzerinden yazar.
"""
from __future__ import annotations

import logging
import os
import time
import uuid
from typing import Any, Dict, Optional

from core.ai.llm_client import LLMClient
from core.memory.db_client import TieredMemoryClient


class BaseDepartmentAgent:
    department: str = "base"

    def __init__(self, workspace_root: str = ".") -> None:
        self.workspace_root = workspace_root
        self.logger = logging.getLogger(f"zom.dept.{self.department}")
        self.llm = LLMClient()
        self.memory = TieredMemoryClient()
        self.memory.department = self.department
        self.current_task_id = None
        from core.zeze_guard.shadow_ceo_alerts import ShadowCEOAlertClient
        self.alerts = ShadowCEOAlertClient()
        from core.ai.critic import CriticAgent
        self.critic = CriticAgent()

        # Wrap execute_task to intercept outcomes and record learnings
        orig_execute = self.execute_task
        async def wrapped_execute(task_data: Dict[str, Any]) -> Dict[str, Any]:
            self._safe_task_id(task_data)
            try:
                res = await orig_execute(task_data)
                await self.record_task_outcome(task_data, res)
                return res
            except Exception as e:
                res = {"success": False, "error": str(e)}
                await self.record_task_outcome(task_data, res)
                raise e
        self.execute_task = wrapped_execute

    def load_manifesto(self) -> str:
        """Loads the department's vision and mission manifesto if it exists."""
        manifesto_path = os.path.join(self.workspace_root, "departments", self.department, "MANIFESTO.md")
        if os.path.exists(manifesto_path):
            try:
                with open(manifesto_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception as e:
                self.logger.error(f"Manifesto okunamadi: {e}")
        return ""

    async def load_knowledge_context(self, task_description: str) -> str:
        """Searches the shared knowledge base for relevant learnings and returns a context block."""
        try:
            from core.knowledge.shared_knowledge import shared_knowledge_base
            items = await shared_knowledge_base.search_knowledge(
                query=task_description[:100],
                limit=3
            )
            if not items:
                return ""
            
            blocks = []
            for item in items:
                blocks.append(f"[{item.type.value.upper()}] {item.title}:\n{item.content}")
            return "\n\n[HOLDING CORPORATE KNOWLEDGE]\n" + "\n---\n".join(blocks)
        except Exception as e:
            self.logger.error(f"Failed to load shared knowledge: {e}")
            return ""

    async def record_task_outcome(self, task_data: Dict[str, Any], result: Dict[str, Any]):
        """Records the outcome of a task to the ROI tracker and registers learnings to the SharedKnowledgeBase."""
        success = result.get("success", False)
        desc = task_data.get("description") or task_data.get("goal") or "Task"
        tid = self.current_task_id or task_data.get("task_id") or "unknown_task"
        
        try:
            from core.zeze_guard.roi_tracker import ROITracker
            tracker = ROITracker()
            tracker.record_outcome(
                agent_id=self.department,
                task_id=tid,
                outcome_type="task",
                success=success,
                metadata={"desc": desc}
            )
        except Exception as e:
            self.logger.error(f"Failed to record outcome to ROITracker: {e}")
            
        try:
            from core.knowledge.shared_knowledge import shared_knowledge_base, KnowledgeItem, KnowledgeType
            from datetime import datetime
            
            outcome_str = "SUCCESS" if success else "FAILURE"
            title = f"{self.department.upper()} {outcome_str}: {desc[:50]}"
            content = f"Task: {desc}\nResult: {outcome_str}\n"
            if success:
                content += f"Execution succeeded. Summary: {result.get('output', 'Completed successfully')}"
                ktype = KnowledgeType.BEST_PRACTICE
            else:
                content += f"Execution failed. Error: {result.get('error', 'Unknown error')}"
                ktype = KnowledgeType.WARNING
                
            item = KnowledgeItem(
                id="",
                type=ktype,
                title=title,
                content=content,
                source_department=self.department,
                tags=[self.department, "learning", outcome_str.lower()],
                confidence=1.0 if success else 0.8,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            await shared_knowledge_base.add_knowledge(item)
        except Exception as e:
            self.logger.error(f"Failed to record learning to SharedKnowledgeBase: {e}")

    async def delegate_task(self, target_department: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Delegates a task dynamically to another department agent in the ZOM ecosystem."""
        self.logger.info(f"Delegating task to {target_department}: {task_data.get('description', '')[:50]}...")
        try:
            module_path = f"departments.{target_department}.agent"
            parts = target_department.split('_')
            class_name = "".join(p.capitalize() for p in parts) + "Agent"
            
            if target_department == "app_factory":
                class_name = "AppFactoryAgent"
            elif target_department == "crypto_trading":
                class_name = "CryptoTradingAgent"
            elif target_department == "media_factory":
                class_name = "MediaFactoryAgent"
                
            module = __import__(module_path, fromlist=[class_name])
            agent_class = getattr(module, class_name)
            agent = agent_class(workspace_root=self.workspace_root)
            
            result = await agent.execute_task(task_data)
            self.logger.info(f"Delegated task completed by {target_department}. Success: {result.get('success', False)}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to delegate task to {target_department}: {e}")
            return {"success": False, "error": str(e)}

    # ── Görev-tipi kapsama altyapısı (eksiksiz yürütme) ─────────────────
    async def dispatch_by_task_type(
        self,
        task_data: Dict[str, Any],
        routes: list,
        default_system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Görev tipini sınıflandırıp ilgili uzman handler'a yönlendirir.

        routes: [(keywords:list[str], handler:async callable), ...]
        Tanınmayan tip → _standard_execute + coverage_miss=True (kör nokta görünür).
        """
        description = (task_data.get("description") or "")
        dl = description.lower()
        explicit = (task_data.get("task_type") or "").lower()

        # 1) Açık task_type eşleşmesi
        if explicit:
            for keywords, handler in routes:
                if explicit in [k.lower() for k in keywords]:
                    return await handler(task_data)
        # 2) Açıklama içi keyword eşleşmesi
        for keywords, handler in routes:
            if any(k in dl for k in keywords):
                return await handler(task_data)

        # 3) Kör nokta: tanınmayan görev tipi → generic, ama needs_review işaretle
        self.logger.warning(
            f"[Coverage] {self.department}: tanınmayan görev tipi → generic fallback. needs_review."
        )
        res = await self._standard_execute(
            task_data, default_system_prompt or f"Sen ZezeLabs {self.department} ajanısın."
        )
        res["coverage_miss"] = True
        res["deliverable"] = False
        try:
            self.alerts.send_alert(
                title=f"Kapsama Açığı: {self.department}",
                message=f"Tanınmayan görev tipi generic'e düştü: {description[:120]}",
                severity="warning",
            )
        except Exception:
            pass
        return res

    def _validate_artifact(self, path: str) -> bool:
        """Artefakt doğrulama (kalite kapısı): var mı + JSON/Python geçerli mi."""
        if not path or not os.path.exists(path):
            return False
        try:
            if path.endswith(".json"):
                import json as _j
                with open(path, "r", encoding="utf-8") as f:
                    _j.load(f)
            elif path.endswith(".py"):
                with open(path, "r", encoding="utf-8") as f:
                    compile(f.read(), path, "exec")
        except Exception as e:
            self.logger.warning(f"[Validate] Artefakt geçersiz {path}: {e}")
            return False
        return True

    # ── Standard contract ───────────────────────────────────────────────
    async def run_cycle(self) -> Dict[str, Any]:
        """Periodic self-execution. Default = noop."""
        return {"status": "noop", "department": self.department}

    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process one task from the orchestrator. Override in subclasses."""
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement execute_task()"
        )

    async def ask_llm(self, prompt: str, system_prompt: str = "You are a helpful AI assistant.") -> str:
        """Helper to invoke the centralized LLM client asynchronously."""
        manifesto = self.load_manifesto()
        if manifesto:
            system_prompt = f"{system_prompt}\n\n[DEPARTMAN MANIFESTOSU]\n{manifesto}"
        
        # Inject dynamic environment context
        system_prompt = system_prompt + self._get_environmental_context()
        
        # Load corporate knowledge context dynamically
        knowledge_context = await self.load_knowledge_context(prompt)
        if knowledge_context:
            system_prompt = f"{system_prompt}\n\n{knowledge_context}"

        try:
            # Politika: basit görev → free, karmaşık görev → Z.ai (glm-5.2)
            from core.ai.model_selector import select_model_for_task
            model = select_model_for_task(prompt, self.department)
        except ImportError:
            model = None

        return await self.llm.generate(
            prompt,
            system_prompt,
            agent_id=self.department,
            task_id=self.current_task_id,
            model=model
        )

    def _get_environmental_context(self) -> str:
        """Generates dynamic environment, workspace, database and tech stack context for the agent prompt."""
        abs_workspace = os.path.abspath(self.workspace_root)
        db_path = os.path.abspath(os.path.join(abs_workspace, "data", "ecosys_memory_v2.db"))
        # Opsiyonel skill kütüphaneleri: dizin yoksa prompt'a ölü yol değil,
        # açık "kurulu değil" işareti yazılır (scratch/ güvenle kaldırılabilir).
        def _opt(*parts: str) -> str:
            p = os.path.abspath(os.path.join(abs_workspace, *parts))
            return p if os.path.isdir(p) else "[KÜTÜPHANE KURULU DEĞİL — bu yeteneği kullanma]"
        superpowers_dir = _opt("docs", "superpowers")
        ecc_dir = _opt("docs", "ecc")
        understand_anything_dir = _opt("scratch", "understand-anything")
        quantmind_dir = _opt("scratch", "quant-mind")
        rowboat_sdk_dir = _opt("rowboat")
        
        context = (
            "\n\n[ENVIRONMENT & RUNTIME CONTEXT]\n"
            f"- HOST OS: Windows (Use Windows path separators '\\\\' or '/' correctly, never assume Unix root like '/data')\n"
            f"- WORKSPACE ROOT PATH (Absolute): {abs_workspace}\n"
            "- AVAILABLE CORE SKILLS: 'file_writer' (writes/modifies workspace files), 'python_executor' (executes Python scripts relative to the workspace and captures stdout/stderr)\n"
            f"- AGENTIC SUPERPOWERS PATH: {superpowers_dir}\n"
            f"- ECC (EVERYTHING CLAUDE CODE) PATH: {ecc_dir}\n"
            "\n[SQLITE MEMORY DATABASE CONFIGURATION]\n"
            f"- DATABASE PATH (Absolute): {db_path}\n"
            "- DATABASE TYPE: SQLite3 with FTS5 virtual table for RAG\n"
            "- TABLE SCHEMAS:\n"
            "  * TABLE memory (\n"
            "      id TEXT PRIMARY KEY,\n"
            "      text TEXT NOT NULL,\n"
            "      metadata TEXT,\n"
            "      tier TEXT DEFAULT 'long',\n"
            "      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n"
            "    )\n"
            "  * VIRTUAL TABLE memory_fts USING fts5 (id UNINDEXED, text)\n"
            "  * TABLE free_programming_books (\n"
            "      id TEXT PRIMARY KEY,\n"
            "      title TEXT NOT NULL,\n"
            "      link TEXT,\n"
            "      description TEXT,\n"
            "      format TEXT,\n"
            "      category TEXT,\n"
            "      language TEXT\n"
            "    )\n"
            "  * VIRTUAL TABLE free_programming_books_fts USING fts5(id UNINDEXED, title, description, category, language)\n"
            "- QUERY INSTRUCTIONS: If you need to perform diagnostics, read or modify the database, write a clean Python script using the 'sqlite3' library and run it using the 'python_executor' tool. Never pretend or report simulated database operations.\n"
            "\n[PROJECT TECHNOLOGY STACK]\n"
            "- BACKEND: Python 3.11+, SQLite (under data/ecosys_memory_v2.db), Uvicorn/FastAPI, RabbitMQ\n"
            "- FRONTEND: React, TypeScript, Vite\n"
            "- CAUTION: Redis and ChromaDB have been COMPLETELY REMOVED from the ecosystem. Never try to use them.\n"
            "\n[SUPERPOWERS AGENTIC SKILLS METHODOLOGY]\n"
            "You MUST follow the professional software engineering discipline defined in the local superpowers skills library:\n"
            "1. Before writing code or modifying files, you MUST load and follow the brainstorming and planning guidelines in:\n"
            "   * {superpowers_dir}\\skills\\brainstorming\\SKILL.md\n"
            "   * {superpowers_dir}\\skills\\writing-plans\\SKILL.md\n"
            "2. During code implementation, you MUST strictly follow the Test-Driven Development (TDD) cycle (Red-Green-Refactor):\n"
            "   * {superpowers_dir}\\skills\\test-driven-development\\SKILL.md\n"
            "   * Principle: Write a failing test first. Verify it fails. Implement minimal code to pass. Verify it passes. Commit.\n"
            "   * Critical Rule: Delete any production code written before its corresponding test exists.\n"
            "3. Before finishing a task, verify your changes by loading the guidelines in:\n"
            "   * {superpowers_dir}\\skills\\verification-before-completion\\SKILL.md\n"
            "\n[EVERYTHING CLAUDE CODE (ECC) SPECIALIZED SKILLS]\n"
            "You have access to 67 specialized agents, 270 workflow skills, and automated rules in the local ECC library:\n"
            f"- ECC ROOT PATH: {ecc_dir}\n"
            "If your task falls under any of these categories, you MUST load and adhere to the respective skill files:\n"
            f"1. Autonomous Trading & Wallet Security: Refer to {ecc_dir}\\skills\\llm-trading-agent-security\\SKILL.md and check prompt injection patterns, daily/single transaction limits, pre-send simulation, and circuit breakers.\n"
            f"2. Coding Standards & Code Quality: Refer to {ecc_dir}\\skills\\coding-standards\\SKILL.md.\n"
            f"3. Database Design & Postgres Migrations: Refer to {ecc_dir}\\skills\\database-migrations\\SKILL.md.\n"
            f"4. FastAPI Patterns: Refer to {ecc_dir}\\skills\\fastapi-patterns\\SKILL.md.\n"
            "\n[UNDERSTAND-ANYTHING CODEBASE INTELLIGENCE & KNOWLEDGE GRAPH]\n"
            "You have access to Egonex-AI/Understand-Anything codebase intelligence tool to analyze, map, and navigate this codebase:\n"
            f"- UNDERSTAND-ANYTHING ROOT PATH: {understand_anything_dir}\n"
            f"- PLUGIN SKILLS PATH: {understand_anything_dir}\\understand-anything-plugin\\skills\n"
            "You can use Understand-Anything CLI commands or plugin skills to generate a structural knowledge graph of this codebase at '.understand-anything/knowledge-graph.json'.\n"
            "Directives:\n"
            "1. When onboarding onto this project or attempting to understand a complex module, you can query/visualize the dependency graph using the '/understand' and '/understand-explain <path>' skills.\n"
            "2. When planning changes, you can use '/understand-diff' to analyze ripple effects across the architecture before modifying files.\n"
            "3. If requested to generate codebase guides, use the '/understand-onboard' or '/understand-domain' tools to capture real domain models and walkthroughs.\n"
            "\n[FREE PROGRAMMING BOOKS & LEARNING RESOURCES]\n"
            "You have access to a large library of free programming books, tutorials, and courses in SQLite table 'free_programming_books':\n"
            "- You can use the 'search_free_books' skill to query resources by topic, programming language, or category.\n"
            "- Directives: When compiling learning curricula, training poor-performing agents, or answering conceptual programming questions, search for real, relevant books/courses from this index and present clickable links to the reader.\n"
            "\n[QUANTMIND FINANCIAL RESEARCH & KNOWLEDGE EXTRACTION]\n"
            "You have access to the QuantMind library for quantitative finance research:\n"
            f"- QUANTMIND ROOT PATH: {quantmind_dir}\n"
            "- You can use the 'extract_quant_strategy' skill to read arXiv quantitative finance papers, parse formulas/sections, and extract structured trading strategies.\n"
            "- Directives: When researching trading models or developing strategies for crypto_trading, use 'extract_quant_strategy' to read academic papers and obtain mathematically precise rule sets.\n"
            "\n[ROWBOAT LOCAL-FIRST AI COWORKER & KNOWLEDGE VAULT]\n"
            "You have access to the Rowboat Obsidian-compatible knowledge graph platform:\n"
            f"- ROWBOAT PYTHON SDK PATH (junction): {rowboat_sdk_dir}\n"
            "- You can use the 'rowboat_chat_turn' skill to query a running Rowboat instance for rich context:\n"
            "  * People profiles, past decisions, open questions, and meeting history\n"
            "  * Project status, roadmap, and commitments\n"
            "  * Meeting prep briefings (e.g., 'Prep me for my meeting with Alex')\n"
            "- Configuration (set via .env or skill parameters):\n"
            "  * ROWBOAT_HOST: Rowboat server address (default: http://localhost:3000)\n"
            "  * ROWBOAT_PROJECT_ID: Rowboat project identifier\n"
            "  * ROWBOAT_API_KEY: Rowboat API key (Bearer token)\n"
            "- Directives: When preparing meeting briefs, drafting emails grounded in context, or building decision logs, use 'rowboat_chat_turn' to query the local knowledge vault.\n"
            "\n[CRITICAL DIRECTIVE: NO SIMULATION / PLACEHOLDERS]\n"
            "- You are a fully autonomous department agent. You must execute real actions. Do not simulate, pretend, or fake actions in markdown or text.\n"
            "- Do not output simulated error tables or fake status summaries saying tools are unavailable. If a task requires writing a file, invoke 'file_writer'. If it requires diagnostics, write a script and run it using 'python_executor'.\n"
            "- The Quality Control unit (CriticAgent) evaluates all results. Any responses with fake summaries, simulated tables, placeholder text, or incorrect JSON formats will be rejected with a failing score (< 70)."
        )
        return context

    async def ask_llm_with_tools(self, prompt: str, system_prompt: str = "You are a helpful AI assistant.") -> str:
        """Helper to invoke the centralized LLM client asynchronously with Tool Calling capabilities."""
        manifesto = self.load_manifesto()
        if manifesto:
            system_prompt = f"{system_prompt}\n\n[DEPARTMAN MANIFESTOSU]\n{manifesto}"
        
        # Inject dynamic environment context
        system_prompt = system_prompt + self._get_environmental_context()

        enforcement = (
            "\n\n[CRITICAL DIRECTIVE: REAL ACTIONS ONLY]\n"
            "You are a real autonomous operating agent. You must never simulate, pretend, or fake actions in text.\n"
            "1. If asked to write code, modify files, or create directories, you MUST call the 'file_writer' tool. Do not just print the file content in markdown.\n"
            "2. If asked to check balance, audit APIs, check configuration, or execute code, you MUST write a python script and run it using the 'python_executor' tool.\n"
            "3. If asked to search information, you MUST call 'duckduckgo_search' or 'web_search'.\n"
            "4. If you cannot complete the task because keys/configurations are missing, write a script to check the keys using 'python_executor' and report the real error output returned by the script. Do not output hypothetical success reports."
        )
        system_prompt_enforced = system_prompt + enforcement
        
        # Load corporate knowledge context dynamically
        knowledge_context = await self.load_knowledge_context(prompt)
        if knowledge_context:
            system_prompt_enforced = f"{system_prompt_enforced}\n\n{knowledge_context}"

        try:
            # Politika: basit görev → free, karmaşık görev → Z.ai (glm-5.2)
            from core.ai.model_selector import select_model_for_task
            model = select_model_for_task(prompt, self.department)
        except ImportError:
            model = None

        if hasattr(self.llm, "generate_with_tools"):
            return await self.llm.generate_with_tools(
                prompt,
                system_prompt_enforced,
                agent_id=self.department,
                task_id=self.current_task_id,
                model=model
            )
        return await self.ask_llm(prompt, system_prompt_enforced)

    async def publish_live_event(self, action: str, status: str, message: str) -> None:
        """Publishes a real-time event to the ZezeLabs Live Activity Stream."""
        try:
            from backend.api.live_stream import event_bus
            await event_bus.publish(
                department=self.department,
                action=action,
                status=status,
                message=message
            )
        except Exception as e:
            self.logger.debug(f"Failed to publish live event to stream: {e}")

    @staticmethod
    def _new_task_id() -> str:
        return str(uuid.uuid4())

    def _safe_task_id(self, task_data: Optional[Dict[str, Any]]) -> str:
        if not task_data:
            tid = self._new_task_id()
        else:
            tid = str(task_data.get("task_id") or self._new_task_id())
        self.current_task_id = tid
        return tid

    async def _standard_execute(
        self,
        task_data: Dict[str, Any],
        system_prompt: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Unified standard execution workflow for ZOM department agents.
        Handles trace monitoring, database RAG, Critic validations, and persists outcomes.
        """
        from core.observability.tracer import Trace
        from datetime import datetime
        import json
        
        task_id = self._safe_task_id(task_data)
        # Öncelik sırası belgelendi: caller'dan gelen explicit description > task_data içindeki description > varsayılan
        effective_description = description or task_data.get("description") or "Detaylı bir analiz ve rapor hazırla."
            
        self.logger.info(f"[{task_id}] Standart görev başlatıldı: {effective_description[:50]}...")
        
        # Start Observability Trace
        trace = Trace(department=self.department, task_description=effective_description)
        
        state_dir = os.path.join(self.workspace_root, "departments", self.department, "reports", task_id)
        os.makedirs(state_dir, exist_ok=True)
        
        # Load past context from vector memory (RAG)
        past_context = self.memory.recall_for_task(effective_description)
        
        full_system_prompt = system_prompt
        if past_context:
            full_system_prompt += f"\n\nŞirket Geçmiş Hafızası:\n{past_context}"
            
        max_retries = 3
        llm_response = ""
        current_description = effective_description
        skip_revision = task_data.get("skip_outer_revision", False)
        
        for attempt in range(max_retries):
            llm_response = await self.ask_llm_with_tools(prompt=current_description, system_prompt=full_system_prompt)
            
            # Critic Evaluation using the pre-initialized CriticAgent instance
            eval_result = await self.critic.evaluate_result(self.department, effective_description, llm_response)
            self.logger.info(f"[{task_id}] Critic Puanı (Deneme {attempt+1}): {eval_result['score']}/100")
            
            if skip_revision or not eval_result.get("needs_revision") or attempt == max_retries - 1:
                trace.set_critic(eval_result['score'], attempt)
                break
                
            self.logger.warning(f"[{task_id}] Critic Revizyon İstedi: {eval_result['feedback']}")
            current_description = effective_description + f"\n\n[ÖNEMLİ REVİZYON TALEBİ! Önceki denemende Kalite Kontrol birimi şu hataları buldu, lütfen bu eleştirilere göre baştan yap:]\n{eval_result['feedback']}"
            
        # Düşük critic skoru → peer departmana delegate et (Faz 1 Unicorn)
        final_score = eval_result.get("score", 0) if eval_result else 0
        if final_score < 60 and not task_data.get("_is_delegated"):
            peer_map = {
                "app_factory": "zeze_dev",
                "zeze_dev": "app_factory",
                "zeze_design": "zeze_rnd",
                "zeze_rnd": "zeze_design",
                "media_factory": "zeze_comms",
                "zeze_comms": "media_factory",
                "zeze_business": "zeze_aro",
                "zeze_aro": "zeze_business",
                "zeze_sec": "zeze_compliance",
                "zeze_compliance": "zeze_sec",
            }
            peer = peer_map.get(self.department)
            if peer:
                self.logger.warning(f"[{task_id}] Critic skoru düşük ({final_score}/100), {peer} departmanına delege ediliyor...")
                try:
                    delegated = await self.delegate_task(peer, {**task_data, "_is_delegated": True})
                    if delegated.get("success"):
                        llm_response = delegated.get("output", llm_response)
                        self.logger.info(f"[{task_id}] Delege başarılı — {peer} sonucu kullanıldı.")
                except Exception as de:
                    self.logger.error(f"[{task_id}] Delege başarısız: {de}")

        # Set actual tokens count from storage or estimate based on characters
        breakdown = self.alerts.storage.get_task_cost_breakdown(task_id)
        actual_tokens = breakdown.get("total_tokens", 0)
        if actual_tokens > 0:
            trace.tokens_estimated = actual_tokens
        else:
            trace.estimate_tokens(effective_description + llm_response)
            
        # Persist memory dynamically (only write high quality score outputs >= 80 to long-term memory)
        critic_score = getattr(trace, "critic_score", 0) or 0
        if not isinstance(critic_score, (int, float)):
            critic_score = 0
        memory_tier = "long" if critic_score >= 80 else "session"
        self.memory.add_memory(
            memory_text=llm_response,
            metadata={"task": effective_description, "dept": self.department, "critic_score": critic_score},
            tier=memory_tier
        )
        
        # Check if PDF quality low warning was triggered during execution (Açık 5)
        risk_level = "low"
        hitl_rule_triggered = None
        if "pdf_quality_low" in llm_response or "[WARNING: PDF QUALITY LOW]" in llm_response:
            risk_level = "high"
            hitl_rule_triggered = "pdf_quality_low"
            self.logger.warning(f"[{task_id}] Low PDF extraction quality detected. Flagging task for HITL approval.")

        report = {
            "task_id": task_id,
            "department": self.department,
            "timestamp": datetime.now().isoformat(),
            "query": effective_description,
            "output": llm_response,
            "status": "completed",
            "trace_id": trace.trace_id,
            "risk_level": risk_level,
            "hitl_rule_triggered": hitl_rule_triggered
        }
        
        report_path = os.path.join(state_dir, "report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        self.logger.info(f"[{task_id}] Rapor oluşturuldu: {report_path}")
        trace.finish(status="success")

        # Deliverable doğrulama (Faz C): standart akış en az rapor dosyası üretir.
        # Boş/çok kısa çıktı gerçek teslim sayılmaz.
        has_real_output = bool(llm_response and len(llm_response.strip()) >= 40)

        return {
            "success": True,
            "report_path": report_path,
            "task_id": task_id,
            "trace_id": trace.trace_id,
            "output": llm_response,
            "artifacts": [report_path],
            "deliverable": has_real_output,
            "risk_level": risk_level,
            "hitl_rule_triggered": hitl_rule_triggered
        }
