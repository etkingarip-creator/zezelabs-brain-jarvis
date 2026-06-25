"""
Zezelabs Holding OS - ZezeBusinessAgent
Gerçek iş zekası: CompetitorScraper (web) + MarketSizer (TAM/SAM hesap) + FinancialModeler.
Deneme yazmaz; gerçek rakip verisi çeker, sayısal pazar modeli üretir, JSON rapor teslim eder.
"""
import os
import re
import json
from typing import Dict, Any
from datetime import datetime
from core.operator_runtime.base_agent import BaseDepartmentAgent


class ZezeBusinessAgent(BaseDepartmentAgent):
    department = "zeze_business"

    def __init__(self, workspace_root: str = "."):
        super().__init__(workspace_root=workspace_root)
        self.workspace_root = os.path.realpath(os.path.abspath(workspace_root))

    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        # Görev-tipi kapsama: pazar/rakip analizi | aksi → generic (needs_review)
        routes = [
            (["pazar", "market", "tam", "sam", "rakip", "competitor", "iş modeli",
              "business model", "strateji", "gelir", "revenue", "büyüme", "growth"],
             self._handle_market_analysis),
        ]
        default_sp = "Sen ZezeLabs İş Geliştirme ajanısın. Pazar analizi, B2B ortaklık, satış stratejisi üretirsin."
        return await self.dispatch_by_task_type(task_data, routes, default_sp)

    async def _handle_market_analysis(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_id = self._safe_task_id(task_data)
        description = task_data.get("description", "") or ""

        from core.skills.registry import SkillRegistry
        registry = SkillRegistry()

        # 1. CompetitorScraper: pazar/rakip web araması
        market_data = ""
        try:
            market_data = await registry.execute_tool(
                "duckduckgo_search",
                {"query": f"{description} market size TAM competitors 2026"}
            )
        except Exception as e:
            self.logger.warning(f"[{task_id}] Pazar araması başarısız: {e}")

        # 2. MarketSizer + FinancialModeler: yapılandırılmış sayısal model
        modeler_prompt = (
            f"GÖREV: '{description}' için iş ve pazar analizi.\n\n"
            f"GERÇEK PAZAR VERİSİ (web):\n{market_data[:2500]}\n\n"
            f"Yukarıdaki gerçek verilere dayanarak SADECE şu JSON formatında yanıt ver:\n"
            f'{{"tam_usd": sayı, "sam_usd": sayı, "som_usd": sayı, '
            f'"top_competitors": ["rakip1","rakip2"], "growth_rate_pct": sayı, '
            f'"strategic_recommendation": "tek paragraf strateji"}}'
        )
        system_prompt = (
            "Sen ZezeLabs İş Geliştirme ajanısın. TAM/SAM/SOM hesaplar, rakip analizi yaparsın. "
            "Sadece sağlanan gerçek veriye dayanırsın; uydurma rakam vermezsin, veri yoksa muhafazakar tahmin yapıp belirtirsin."
        )
        llm_response = await self.ask_llm(modeler_prompt, system_prompt=system_prompt)

        model: Dict[str, Any] = {}
        try:
            m = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if m:
                model = json.loads(m.group(0))
        except Exception:
            model = {"strategic_recommendation": llm_response[:300]}

        # 3. Deliverable: iş planı raporu
        report = {
            "task_id": task_id,
            "department": self.department,
            "timestamp": datetime.now().isoformat(),
            "query": description,
            "market_sources": market_data[:1500],
            "model": model,
        }
        report_dir = os.path.join(self.workspace_root, "departments", self.department, "reports", task_id)
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, "business_model.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        def _fmt(v):
            try:
                return f"${float(v):,.0f}"
            except Exception:
                return str(v)

        output = (
            f"# İş & Pazar Analizi\n\n"
            f"**Konu:** {description}\n"
            f"- **TAM:** {_fmt(model.get('tam_usd', 'N/A'))}\n"
            f"- **SAM:** {_fmt(model.get('sam_usd', 'N/A'))}\n"
            f"- **SOM:** {_fmt(model.get('som_usd', 'N/A'))}\n"
            f"- **Büyüme:** %{model.get('growth_rate_pct', 'N/A')}\n"
            f"- **Rakipler:** {', '.join(str(x) for x in model.get('top_competitors', []))}\n\n"
            f"**Strateji:** {model.get('strategic_recommendation', 'N/A')}"
        )
        return {
            "success": True,
            "task_id": task_id,
            "output": output,
            "artifacts": [report_path],
            "deliverable": True,
        }
