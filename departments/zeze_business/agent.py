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

        # 2. LLM artık nihai sayı değil GİRDİ/VARSAYIM verir; motor HESAPLAR (halüsinasyon yerine matematik)
        modeler_prompt = (
            f"GÖREV: '{description}' için iş analizi girdileri.\n\n"
            f"GERÇEK PAZAR VERİSİ (web):\n{market_data[:2500]}\n\n"
            f"Gerçek veriye dayanarak iş matematiği GİRDİLERİNİ ver (nihai TAM/SAM/SOM'u SEN hesaplama, "
            f"biz hesaplayacağız). SADECE JSON:\n"
            f'{{"top_down_tam_usd": sayı, "target_users": sayı, "conversion_pct": sayı, '
            f'"price_monthly": sayı, "gross_margin_pct": sayı, "cac": sayı, "churn_monthly_pct": sayı, '
            f'"ai_cogs_monthly": sayı, "ai_cogs_per_use": sayı, "usage_predictability": "öngörülebilir|değişken", '
            f'"target": "b2c|b2b", "top_competitors": ["r1","r2"], "growth_rate_pct": sayı}}'
        )
        system_prompt = (
            "Sen ZezeLabs İş Geliştirme ajanısın. Gerçek veriye dayalı GİRDİ varsayımları verirsin "
            "(fiyat, marj, CAC, churn, AI compute maliyeti). Uydurma; veri yoksa muhafazakar varsay ve belirt."
        )
        llm_response = await self.ask_llm(modeler_prompt, system_prompt=system_prompt)

        inputs: Dict[str, Any] = {}
        try:
            m = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if m:
                inputs = json.loads(m.group(0))
        except Exception:
            inputs = {}

        # 3. MOTOR HESABI — doğrulanabilir iş matematiği (G1-G3)
        from departments.zeze_business import business_engine as be

        def _num(k, d=0.0):
            try:
                return float(inputs.get(k, d))
            except (TypeError, ValueError):
                return d

        model: Dict[str, Any] = {"top_competitors": inputs.get("top_competitors", []),
                                 "growth_rate_pct": inputs.get("growth_rate_pct", "N/A")}
        ue = be.unit_economics(_num("price_monthly"), _num("gross_margin_pct", 70), _num("cac"),
                               _num("churn_monthly_pct", 5), _num("ai_cogs_monthly"))
        som = be.bottom_up_som(int(_num("target_users")), _num("conversion_pct", 2), _num("price_monthly"))
        tam = _num("top_down_tam_usd")
        reco = be.reconcile_market(tam, som["som_arr_usd"]) if tam else {"note": "TAM verisi yok"}
        mon = be.select_monetization(_num("ai_cogs_per_use"), inputs.get("usage_predictability", "değişken"),
                                     inputs.get("target", "b2c"))
        model.update({"unit_economics": ue, "bottom_up_som": som, "top_down_tam_usd": tam,
                      "reconciliation": reco, "monetization": mon})
        # G4 ANTİ-SAHTE-YEŞİL: motor geçerli unit economics üretemezse başarı sayma
        analysis_valid = ue.get("valid", False) and som["paying_customers"] >= 0

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

        ue = model["unit_economics"]
        som = model["bottom_up_som"]
        mon = model["monetization"]
        ue_line = (f"LTV/CAC {ue.get('ltv_cac_ratio')} | payback {ue.get('payback_months')}ay | "
                   f"AI-sonrası marj %{ue.get('margin_after_ai_pct')} | sağlıklı: {'✅' if ue.get('healthy') else '❌'}") \
            if ue.get("valid") else "girdi yetersiz"
        warn = ("\n".join(f"  ⚠️ {x}" for x in ue.get("warnings", []))) if ue.get("warnings") else ""
        output = (
            f"# İş & Pazar Analizi (hesaplanmış — halüsinasyon değil)\n\n"
            f"**Konu:** {description}\n\n"
            f"## Pazar (top-down + bottom-up)\n"
            f"- **Top-down TAM:** {_fmt(model.get('top_down_tam_usd', 'N/A'))}\n"
            f"- **Bottom-up SOM:** {_fmt(som['som_arr_usd'])} ARR ({som['paying_customers']} ödeyen müşteri)\n"
            f"  - Varsayım: {som['assumptions']}\n"
            f"  - Tutarlılık: {model['reconciliation'].get('note')}\n\n"
            f"## Unit Economics (AI COGS dahil — Replit dersi)\n- {ue_line}\n{warn}\n\n"
            f"## Monetizasyon\n- **Model:** {mon['recommended_model']}\n  - {mon['rationale']}\n\n"
            f"**Rakipler:** {', '.join(str(x) for x in model.get('top_competitors', []))} | Büyüme: %{model.get('growth_rate_pct','N/A')}"
        )
        return {
            "success": analysis_valid,
            "task_id": task_id,
            "output": output,
            "artifacts": [report_path],
            "deliverable": analysis_valid,
        }
