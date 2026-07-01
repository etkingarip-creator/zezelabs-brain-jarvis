import os
import re
import json
import logging
import uuid
import asyncio
from typing import Dict, Any, List, Optional
from core.config import config
from core.mq_client import MQClient
from core.memory.db_client import TieredMemoryClient
from core.ai.providers.openrouter_director import get_openrouter_director

class CognitiveRouter:
    """
    ZOM Super-Intelligence Core (v2.0)
    Gemini KALDIRILDI - OpenRouter Llama kullanılıyor
    """
    def __init__(self):
        self.mq = MQClient(
            host=config.RABBITMQ_HOST,
            port=config.RABBITMQ_PORT,
            user=config.RABBITMQ_USER,
            password=config.RABBITMQ_PASS,
        )
        self.memory = TieredMemoryClient()
        self.logger = logging.getLogger("zom.cognitive_router")
        
        self.system_instruction = """
Sen Zezelabs Holding'in 'Omni-Orchestrator' adlı süper zekasısın. 
Görevin: Karmaşık kullanıcı taleplerini analiz etmek, holding departmanlarını koordine etmek ve MÜKEMMEL bir operasyonel plan hazırlamaktır.

HOLDİNG ANAYASASI:
1. Asla 'bilmiyorum' deme, departmanları kullanarak çözüm üret.
2. Her adımda verimliliği ve hızı maksimize et.
3. Geçmiş hatalardan (Self-Audit) ders çıkar.

DEPARTMAN YETENEKLERİ (17 departman — TEK KAYNAK: core.registry.routing):
""" + __import__("core.registry.routing", fromlist=["departments_brief"]).departments_brief() + """
NOT: Video/short/seyahat/içerik → media_factory. Grafik/UI/logo → zeze_design (video değil).

PLANLAMA PROTOKOLÜ:
Önce içinden düşün (Reasoning), sonra planı JSON formatında sun.
"""

    async def orchestrate(self, user_prompt: str, context: Optional[Dict] = None):
        self.logger.info(f"🧠 Advanced Cognitive Orchestration: {user_prompt[:50]}...")
        
        past_experiences = self.memory.recall_for_task(user_prompt)
        self_awareness = self.memory.recall_for_task("audit_log fix_suggestion")

        # Hafiza bos uyarisi ekle
        memory_warning = ""
        if not past_experiences:
            memory_warning = "\n⚠️ UYARI: Bu konuda gecmis veri yok. Sadece dogrulanmis bilgi kullan, spekulatif iceerik uretme."
            self.logger.warning("⚠️ Hafiza bos — AI spekulatif senaryo uretebilir!")
        
        planning_prompt = f"""
GÖREV: {user_prompt}

KAPSAM:
- Gecmis Deneyimler: {past_experiences or "YOK"}
- Öz-Denetim Verileri: {self_awareness or "YOK"}
{memory_warning}

TALİMAT: Önce 'REASONING' basligi altinda adim adim muhakeme yap, ardindan 'JSON_PLAN' basligi altinda plani ver.

JSON ŞABLONU:
{{
    "analysis": "Kısa stratejik analiz",
    "plan": [
        {{ "step": 1, "agent": "...", "task": "..." }}
    ],
    "goal": "Görevin nihai hedefi"
}}
"""
        
        try:
            response = await get_openrouter_director().chat(
                message=planning_prompt,
                system=self.system_instruction,
                use_fast=False
            )
            
            # Extract reasoning and json
            reasoning = ""
            if "JSON_PLAN" in response:
                reasoning = response.split("JSON_PLAN")[0].replace("REASONING", "").strip()
            
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                raise ValueError("JSON Plan not found in response")
                
            plan_data = json.loads(json_match.group(0))
            self.logger.info(f"✅ Plan extracted after reasoning.")
            
            # 3. Execution (Dispatching)
            execution_results = []
            parent_task_id = str(uuid.uuid4())
            
            for step in plan_data.get("plan", []):
                task_id = f"{parent_task_id}_{step['step']}"
                payload = {
                    "task_id": task_id,
                    "parent_id": parent_task_id,
                    "sender": "orchestrator",
                    "agent": step["agent"],
                    "description": step["task"],
                    "depends_on": step.get("depends_on", []),
                    "context": context or {},
                    "plan_step": step["step"]
                }
                
                queue_name = f"zeze_{step['agent']}_queue"
                if self.mq.publish(queue_name, payload):
                    execution_results.append({"step": step["step"], "status": "dispatched", "task_id": task_id})
                else:
                    execution_results.append({"step": step["step"], "status": "failed"})

            return {
                "parent_task_id": parent_task_id,
                "reasoning": reasoning,
                "analysis": plan_data.get("analysis", ""),
                "steps": execution_results
            }

        except Exception as e:
            self.logger.exception(f"❌ Orchestration Error: {e}")
            return {"status": "error", "error": str(e)}

    async def decompose_and_execute(
        self,
        description: str,
        agents: Dict[str, Any],  # {dept_name: agent_instance}
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Görevi LLM ile paralel alt-görevlere ayır ve asyncio.gather() ile çalıştır.
        Unicorn Faz 3 — Gerçek paralel çok-ajan yürütme.
        """
        planning_prompt = f"""
Aşağıdaki görevi birden fazla departmanın PARALEL olarak çalışabileceği alt-görevlere ayır.
GÖREV: {description}

MEVCUT DEPARTMANLAR: {", ".join(agents.keys())}

JSON şablonu (sadece JSON döndür):
{{
  "parallel_tasks": [
    {{"department": "dept_name", "subtask": "bu departmanın yapacağı iş"}}
  ]
}}
"""
        try:
            response = await get_openrouter_director().chat(
                message=planning_prompt,
                system=self.system_instruction,
                use_fast=True,
            )
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                raise ValueError("Decomposition JSON not found")
            plan = json.loads(json_match.group(0))
            parallel_tasks = plan.get("parallel_tasks", [])
        except Exception as e:
            self.logger.warning(f"Decomposition failed ({e}), fallback to single-agent")
            return await self.orchestrate(description, context)

        valid_tasks = [(t["department"], t["subtask"]) for t in parallel_tasks if t.get("department") in agents]
        if not valid_tasks:
            return await self.orchestrate(description, context)

        self.logger.info(f"[Decompose] {len(valid_tasks)} paralel görev başlatılıyor: {[t[0] for t in valid_tasks]}")

        async def _run_one(dept: str, subtask: str) -> Dict[str, Any]:
            agent = agents[dept]
            task_data = {"task_id": str(uuid.uuid4()), "description": subtask, **(context or {})}
            try:
                result = await agent.execute_task(task_data)
                return {"department": dept, "success": True, "output": result.get("output", "")}
            except Exception as ex:
                return {"department": dept, "success": False, "error": str(ex)}

        results = await asyncio.gather(*[_run_one(d, s) for d, s in valid_tasks], return_exceptions=False)
        return {"parallel_results": results, "departments": [t[0] for t in valid_tasks]}


if __name__ == "__main__":
    # Test run
    logging.basicConfig(level=logging.INFO)
    router = CognitiveRouter()
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(router.orchestrate("Yeni bir kripto projesi için pazar analizi yap ve buna uygun bir sosyal medya stratejisi geliştir."))
    print(json.dumps(res, indent=2))
