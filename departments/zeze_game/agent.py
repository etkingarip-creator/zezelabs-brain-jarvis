"""
Zezelabs Holding OS - ZezeGameAgent
Gerçek oyun tasarımı: MechanicsDesigner — yapılandırılmış oyun tasarım belgesi + config üretir.
Deneme yazmaz; mekanik/loop/monetizasyon JSON config'i diske teslim eder.
"""
import os
import re
import json
from typing import Dict, Any
from datetime import datetime
from core.operator_runtime.base_agent import BaseDepartmentAgent


class ZezeGameAgent(BaseDepartmentAgent):
    department = "zeze_game"

    def __init__(self, workspace_root: str = "."):
        super().__init__(workspace_root=workspace_root)
        self.workspace_root = os.path.realpath(os.path.abspath(workspace_root))

    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        # Görev-tipi kapsama: alan içi → uzman handler; tanınmazsa generic (needs_review)
        routes = [(["oyun", "game", "mekanik", "level", "oynanış", "monetiz", "karakter", "gameplay"], self._handle_primary)]
        return await self.dispatch_by_task_type(task_data, routes, 'Sen ZezeLabs Oyun Tasarımı ajanısın. Oynanış ve monetizasyon tasarlarsın.')

    async def _handle_primary(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_id = self._safe_task_id(task_data)
        description = task_data.get("description", "") or ""

        designer_prompt = (
            f"GÖREV: {description}\n\n"
            f"Bir oyun tasarımcısı olarak yapılandırılmış, uygulanabilir oyun tasarım belgesi üret.\n"
            f"SADECE şu JSON formatında yanıt ver:\n"
            f'{{"title": "oyun adı", "core_loop": ["adım1","adım2","adım3"], '
            f'"mechanics": ["mekanik1","mekanik2"], "progression": "ilerleme sistemi", '
            f'"monetization": ["model1","model2"], "engagement_hooks": ["kanca1","kanca2"], '
            f'"target_audience": "hedef kitle"}}'
        )
        system_prompt = "Sen ZezeLabs Oyun Tasarımı ajanısın. Oyuncu psikolojisi ve engagement loop'larına dayalı uygulanabilir tasarım üretirsin."
        llm_response = await self.ask_llm(designer_prompt, system_prompt=system_prompt)

        gdd: Dict[str, Any] = {}
        try:
            m = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if m:
                gdd = json.loads(m.group(0))
        except Exception:
            gdd = {"title": "N/A", "core_loop": [llm_response[:200]]}

        report = {
            "task_id": task_id, "department": self.department,
            "timestamp": datetime.now().isoformat(), "query": description,
            "game_design": gdd,
        }
        report_dir = os.path.join(self.workspace_root, "departments", self.department, "reports", task_id)
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, "game_design_doc.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        output = (
            f"# Oyun Tasarım Belgesi: {gdd.get('title', 'N/A')}\n\n"
            f"**Görev:** {description}\n"
            f"- **Çekirdek Döngü:** {' → '.join(str(x) for x in gdd.get('core_loop', []))}\n"
            f"- **Mekanikler:** {', '.join(str(x) for x in gdd.get('mechanics', []))}\n"
            f"- **Monetizasyon:** {', '.join(str(x) for x in gdd.get('monetization', []))}\n"
            f"- **Engagement:** {', '.join(str(x) for x in gdd.get('engagement_hooks', []))}\n"
            f"- **Hedef Kitle:** {gdd.get('target_audience', 'N/A')}"
        )
        return {
            "success": True, "task_id": task_id, "output": output,
            "artifacts": [report_path], "deliverable": True,
        }
