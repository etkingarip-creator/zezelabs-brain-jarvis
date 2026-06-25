"""
Zezelabs Holding OS - ZezeOpsAgent
Gerçek operasyon: MetricsCollector (canlı sistem metrikleri) + AutoOptimizer (öneri).
Deneme yazmaz; gerçek sistem metriği toplar, optimizasyon planı üretir, JSON rapor teslim eder.
"""
import os
import re
import json
from typing import Dict, Any
from datetime import datetime
from core.operator_runtime.base_agent import BaseDepartmentAgent


class ZezeOpsAgent(BaseDepartmentAgent):
    department = "zeze_ops"

    def __init__(self, workspace_root: str = "."):
        super().__init__(workspace_root=workspace_root)
        self.workspace_root = os.path.realpath(os.path.abspath(workspace_root))

    def _collect_metrics(self) -> Dict[str, Any]:
        """MetricsCollector: gerçek sistem metriklerini topla."""
        metrics: Dict[str, Any] = {}
        try:
            import psutil
            metrics = {
                "cpu_percent": psutil.cpu_percent(interval=0.5),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage(os.getcwd()).percent,
                "process_count": len(psutil.pids()),
            }
        except Exception as e:
            metrics = {"error": f"psutil unavailable: {e}"}
        return metrics

    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        # Görev-tipi kapsama: alan içi → uzman handler; tanınmazsa generic (needs_review)
        routes = [(["operasyon", "sistem", "denetim", "metrik", "optimiz", "süreç", "kpi", "verimlilik", "performans", "darboğaz"], self._handle_primary)]
        return await self.dispatch_by_task_type(task_data, routes, 'Sen ZezeLabs Operasyon ajanısın. Sistem metriği ve optimizasyon üretirsin.')

    async def _handle_primary(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_id = self._safe_task_id(task_data)
        description = task_data.get("description", "") or ""

        # 1. MetricsCollector: gerçek metrikler
        metrics = self._collect_metrics()

        # 2. AutoOptimizer: metriklere dayalı optimizasyon planı
        opt_prompt = (
            f"GÖREV: {description}\n\n"
            f"CANLI SİSTEM METRİKLERİ:\n{json.dumps(metrics, indent=2)}\n\n"
            f"Bu gerçek metriklere dayanarak SADECE şu JSON formatında yanıt ver:\n"
            f'{{"bottlenecks": ["darboğaz1"], "kpis": {{"hedef_metrik": "değer"}}, '
            f'"action_items": ["aksiyon1","aksiyon2"], "priority": "high/medium/low"}}'
        )
        system_prompt = "Sen ZezeLabs Operasyon ajanısın. Gerçek metriklere dayanarak somut KPI ve optimizasyon aksiyonları üretirsin."
        llm_response = await self.ask_llm(opt_prompt, system_prompt=system_prompt)

        plan: Dict[str, Any] = {}
        try:
            m = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if m:
                plan = json.loads(m.group(0))
        except Exception:
            plan = {"action_items": [llm_response[:200]]}

        report = {
            "task_id": task_id, "department": self.department,
            "timestamp": datetime.now().isoformat(), "query": description,
            "live_metrics": metrics, "optimization_plan": plan,
        }
        report_dir = os.path.join(self.workspace_root, "departments", self.department, "reports", task_id)
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, "ops_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        output = (
            f"# Operasyon Raporu\n\n"
            f"**Görev:** {description}\n\n"
            f"## Canlı Metrikler\n"
            f"- CPU: %{metrics.get('cpu_percent', 'N/A')} | RAM: %{metrics.get('memory_percent', 'N/A')} | Disk: %{metrics.get('disk_percent', 'N/A')}\n\n"
            f"## Darboğazlar\n{', '.join(str(x) for x in plan.get('bottlenecks', []))}\n\n"
            f"## Aksiyonlar ({plan.get('priority', 'N/A')} öncelik)\n"
            + "\n".join(f"- {a}" for a in plan.get('action_items', []))
        )
        return {
            "success": True, "task_id": task_id, "output": output,
            "artifacts": [report_path], "deliverable": True,
        }
