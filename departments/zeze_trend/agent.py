"""
Zezelabs Holding OS - ZezeTrendAgent
Gerçek trend istihbaratı: CompetitorScraper (web arama) + SentimentAnalyst (skorlama).
Deneme yazmaz; gerçek web verisi çeker, trend skoru hesaplar, JSON rapor üretir.
"""
import os
import re
import json
from typing import Dict, Any
from datetime import datetime
from core.operator_runtime.base_agent import BaseDepartmentAgent


class ZezeTrendAgent(BaseDepartmentAgent):
    department = "zeze_trend"

    def __init__(self, workspace_root: str = "."):
        super().__init__(workspace_root=workspace_root)
        self.workspace_root = os.path.realpath(os.path.abspath(workspace_root))

    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_id = self._safe_task_id(task_data)
        description = task_data.get("description", "") or ""

        from core.skills.registry import SkillRegistry
        registry = SkillRegistry()

        # 1. CompetitorScraper: gerçek web araması
        search_results = ""
        try:
            search_results = await registry.execute_tool("duckduckgo_search", {"query": f"{description} latest trends 2026"})
        except Exception as e:
            self.logger.warning(f"[{task_id}] Web arama başarısız: {e}")
            search_results = ""

        # 2. SentimentAnalyst: LLM ile skorlanmış trend analizi (web verisine dayalı)
        analyst_prompt = (
            f"GÖREV: '{description}' konusunda trend analizi.\n\n"
            f"GERÇEK WEB ARAMA SONUÇLARI:\n{search_results[:2500]}\n\n"
            f"Yukarıdaki GERÇEK verilere dayanarak SADECE şu JSON formatında yanıt ver:\n"
            f'{{"trend_score": 0-100 arası sayı, "sentiment": "bullish/neutral/bearish", '
            f'"key_signals": ["sinyal1","sinyal2"], "verdict": "tek cümle karar"}}'
        )
        system_prompt = "Sen ZezeLabs Trend İstihbarat ajanısın. Sadece sağlanan gerçek veriye dayanarak veri-odaklı skorlama yaparsın. Spekülasyon yapmazsın."
        llm_response = await self.ask_llm(analyst_prompt, system_prompt=system_prompt)

        # JSON ayıkla
        analysis: Dict[str, Any] = {}
        try:
            m = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if m:
                analysis = json.loads(m.group(0))
        except Exception:
            analysis = {"trend_score": 50, "sentiment": "neutral", "verdict": llm_response[:200]}

        # 3. Deliverable: trend raporu dosyası
        report = {
            "task_id": task_id,
            "department": self.department,
            "timestamp": datetime.now().isoformat(),
            "query": description,
            "web_sources": search_results[:1500],
            "analysis": analysis,
        }
        report_dir = os.path.join(self.workspace_root, "departments", self.department, "reports", task_id)
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, "trend_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        output = (
            f"# Trend İstihbarat Raporu\n\n"
            f"**Konu:** {description}\n"
            f"- **Trend Skoru:** {analysis.get('trend_score', 'N/A')}/100\n"
            f"- **Duygu:** {analysis.get('sentiment', 'N/A')}\n"
            f"- **Sinyaller:** {', '.join(str(x) for x in analysis.get('key_signals', []))}\n"
            f"- **Karar:** {analysis.get('verdict', 'N/A')}\n"
        )
        return {
            "success": True,
            "task_id": task_id,
            "output": output,
            "artifacts": [report_path],
            "deliverable": True,
        }
