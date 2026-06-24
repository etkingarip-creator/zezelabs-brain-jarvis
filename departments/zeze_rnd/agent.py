"""
Zezelabs Holding OS - ZezeRndAgent
Refactored using standard execution pattern
"""
import os
from typing import Dict, Any
from core.operator_runtime.base_agent import BaseDepartmentAgent

class ZezeRndAgent(BaseDepartmentAgent):
    department = "zeze_rnd"
    
    def __init__(self, workspace_root: str = "."):
        super().__init__(workspace_root=workspace_root)
        self.workspace_root = os.path.realpath(os.path.abspath(workspace_root))
    
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        description = (task_data.get("description", "") or "").lower()

        # Trend tarama / prototip / teknoloji keşfi niyeti → GERÇEK pipeline (Scout→Sandbox→Injector)
        pipeline_keywords = [
            "trend", "tara", "scout", "prototip", "prototype", "yeni teknoloji",
            "araştır ve test", "keşfet", "entegre et", "model dene", "poc", "kanıt"
        ]
        if any(kw in description for kw in pipeline_keywords):
            self.logger.info("[zeze_rnd] Ar-Ge pipeline niyeti tespit edildi → Scout→Sandbox→Injector çalıştırılıyor.")
            task_id = self._safe_task_id(task_data)
            try:
                pipeline_result = await self.run_cycle()
                trend = pipeline_result.get("trend", {})
                sandbox = pipeline_result.get("sandbox", {})
                injection = pipeline_result.get("injection", {})

                output = (
                    f"# Ar-Ge Pipeline Raporu\n\n"
                    f"## 1. Tespit Edilen Trend\n"
                    f"- **Başlık:** {trend.get('title', 'N/A')}\n"
                    f"- **Skor:** {trend.get('score', 'N/A')}\n\n"
                    f"## 2. Sandbox Test Sonucu\n"
                    f"- **Geçti mi:** {sandbox.get('passed', False)}\n"
                    f"- **Detay:** {sandbox.get('summary', sandbox)}\n\n"
                    f"## 3. Entegrasyon\n"
                    f"- **Durum:** {injection.get('status', 'atlandı') if injection else 'sandbox geçmedi'}\n"
                )

                # Deliverable: rapor dosyasını yaz
                import os, json
                report_dir = os.path.join(self.workspace_root, "departments", self.department, "reports", task_id)
                os.makedirs(report_dir, exist_ok=True)
                report_path = os.path.join(report_dir, "rnd_pipeline_report.json")
                with open(report_path, "w", encoding="utf-8") as f:
                    json.dump(pipeline_result, f, indent=2, ensure_ascii=False, default=str)

                return {
                    "success": True,
                    "task_id": task_id,
                    "output": output,
                    "artifacts": [report_path],
                    "deliverable": True,
                }
            except Exception as e:
                self.logger.error(f"[zeze_rnd] Pipeline hatası: {e}. Standart akışa düşülüyor.")

        system_prompt = "Sen ZezeLabs R&D (Ar-Ge) ajanısın. Yenilikçi çözümler araştırır, teknoloji trendlerini inceler ve Ar-Ge stratejileri, prototip fikirleri geliştirirsin. Hipotez kurarsın, kaynakça araştırması yaparsın ve bulguları raporlarsın."
        return await self._standard_execute(task_data, system_prompt)

    async def run_cycle(self) -> Dict[str, Any]:
        """
        Run the complete pipeline: The Scout -> Sandbox Engineer -> Injector.
        """
        from core.ai.providers.trend_scout import TrendScout
        from core.ai.providers.sandbox_engineer import SandboxEngineer
        from core.ai.providers.injector import Injector

        trend_scout = TrendScout()
        sandbox_engineer = SandboxEngineer()
        injector = Injector()

        # 1. Scan
        trends = await trend_scout.scan()
        top_trend = trends[0] if trends else {"title": "Kokoro-TTS", "score": 0.95}
        
        # 2. Test
        test_result = await sandbox_engineer.test(top_trend)
        
        # 3. Inject
        injection_result = {}
        if test_result.get("passed", False):
            injection_result = await injector.inject(top_trend)
            
        # Close connection resources
        await trend_scout.close()

        return {
            "trend": top_trend,
            "sandbox": test_result,
            "injection": injection_result
        }
