"""
Zezelabs Holding OS - ZezeComplianceAgent
Gerçek uyumluluk denetimi: PolicyAuditor — kural bazlı denetim listesi + risk skoru üretir.
Deneme yazmaz; yapılandırılmış denetim raporu (kural/durum/risk) diske teslim eder.
"""
import os
import re
import json
from typing import Dict, Any
from datetime import datetime
from core.operator_runtime.base_agent import BaseDepartmentAgent


class ZezeComplianceAgent(BaseDepartmentAgent):
    department = "zeze_compliance"

    def __init__(self, workspace_root: str = "."):
        super().__init__(workspace_root=workspace_root)
        self.workspace_root = os.path.realpath(os.path.abspath(workspace_root))

    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        # Görev-tipi kapsama: alan içi → uzman handler; tanınmazsa generic (needs_review)
        routes = [(["uyum", "compliance", "kvkk", "gdpr", "yasal", "denetim", "politika", "risk", "mevzuat"], self._handle_primary)]
        return await self.dispatch_by_task_type(task_data, routes, 'Sen ZezeLabs Uyumluluk ajanısın. KVKK/GDPR denetimi yaparsın.')

    async def _handle_primary(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_id = self._safe_task_id(task_data)
        description = task_data.get("description", "") or ""

        auditor_prompt = (
            f"GÖREV: {description}\n\n"
            f"Bir uyumluluk denetçisi olarak KVKK/GDPR ve şirket politikaları açısından denetim yap.\n"
            f"SADECE şu JSON formatında yanıt ver:\n"
            f'{{"checklist": [{{"rule": "kural", "status": "compliant/non_compliant/needs_review", '
            f'"risk": "high/medium/low", "remediation": "düzeltme"}}], '
            f'"overall_risk_score": 0-100, "verdict": "tek cümle karar"}}'
        )
        system_prompt = "Sen ZezeLabs Uyumluluk ajanısın. Hukuki uyum, KVKK/GDPR ve risk denetimi yaparsın. Belirsiz ifade kullanmazsın; her kuralı net statüye bağlarsın."
        llm_response = await self.ask_llm(auditor_prompt, system_prompt=system_prompt)

        audit: Dict[str, Any] = {}
        try:
            m = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if m:
                audit = json.loads(m.group(0))
        except Exception:
            audit = {"checklist": [], "verdict": llm_response[:200]}

        report = {
            "task_id": task_id, "department": self.department,
            "timestamp": datetime.now().isoformat(), "query": description,
            "audit": audit,
        }
        report_dir = os.path.join(self.workspace_root, "departments", self.department, "reports", task_id)
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, "compliance_audit.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        checklist = audit.get("checklist", [])
        check_lines = "\n".join(
            f"- [{c.get('status','?')}] {c.get('rule','?')} (risk: {c.get('risk','?')})"
            for c in checklist if isinstance(c, dict)
        )
        output = (
            f"# Uyumluluk Denetim Raporu\n\n"
            f"**Görev:** {description}\n"
            f"**Genel Risk Skoru:** {audit.get('overall_risk_score', 'N/A')}/100\n\n"
            f"## Denetim Listesi\n{check_lines}\n\n"
            f"**Karar:** {audit.get('verdict', 'N/A')}"
        )
        return {
            "success": True, "task_id": task_id, "output": output,
            "artifacts": [report_path], "deliverable": True,
        }
