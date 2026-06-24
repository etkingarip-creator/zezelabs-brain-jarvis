"""
Zezelabs Holding OS - ZezeProductionAgent
Gerçek üretim planlama: AssetBuilder — ölçülebilir üretim planı + kontrol listesi üretir.
Deneme yazmaz; yapılandırılmış üretim planı JSON'ı diske teslim eder.
"""
import os
import re
import json
from typing import Dict, Any
from datetime import datetime
from core.operator_runtime.base_agent import BaseDepartmentAgent


class ZezeProductionAgent(BaseDepartmentAgent):
    department = "zeze_production"

    def __init__(self, workspace_root: str = "."):
        super().__init__(workspace_root=workspace_root)
        self.workspace_root = os.path.realpath(os.path.abspath(workspace_root))

    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_id = self._safe_task_id(task_data)
        description = task_data.get("description", "") or ""

        planner_prompt = (
            f"GÖREV: {description}\n\n"
            f"Bir üretim planlama uzmanı olarak ölçülebilir, aşamalı üretim planı üret.\n"
            f"SADECE şu JSON formatında yanıt ver:\n"
            f'{{"phases": [{{"name": "aşama", "duration_days": sayı, "deliverable": "çıktı"}}], '
            f'"quality_gates": ["kontrol1","kontrol2"], "resources_needed": ["kaynak1"], '
            f'"total_duration_days": sayı, "risk_factors": ["risk1"]}}'
        )
        system_prompt = "Sen ZezeLabs Üretim ajanısın. Üretim planlaması, kalite kontrol ve tedarik zinciri için ölçülebilir planlar üretirsin."
        llm_response = await self.ask_llm(planner_prompt, system_prompt=system_prompt)

        plan: Dict[str, Any] = {}
        try:
            m = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if m:
                plan = json.loads(m.group(0))
        except Exception:
            plan = {"phases": [], "risk_factors": [llm_response[:200]]}

        report = {
            "task_id": task_id, "department": self.department,
            "timestamp": datetime.now().isoformat(), "query": description,
            "production_plan": plan,
        }
        report_dir = os.path.join(self.workspace_root, "departments", self.department, "reports", task_id)
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, "production_plan.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        phases = plan.get("phases", [])
        phase_lines = "\n".join(
            f"- **{p.get('name','?')}** ({p.get('duration_days','?')} gün): {p.get('deliverable','?')}"
            for p in phases if isinstance(p, dict)
        )
        output = (
            f"# Üretim Planı\n\n"
            f"**Görev:** {description}\n"
            f"**Toplam Süre:** {plan.get('total_duration_days', 'N/A')} gün\n\n"
            f"## Aşamalar\n{phase_lines}\n\n"
            f"## Kalite Kapıları\n{', '.join(str(x) for x in plan.get('quality_gates', []))}\n\n"
            f"## Riskler\n{', '.join(str(x) for x in plan.get('risk_factors', []))}"
        )
        return {
            "success": True, "task_id": task_id, "output": output,
            "artifacts": [report_path], "deliverable": True,
        }
