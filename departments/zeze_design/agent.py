"""
Zezelabs Holding OS - ZezeDesignAgent
Gerçek LLM Entegrasyonlu Ajan
"""
import os
import json
from typing import Dict, Any
from datetime import datetime
from core.operator_runtime.base_agent import BaseDepartmentAgent
from core.observability.tracer import Trace

class ZezeDesignAgent(BaseDepartmentAgent):
    department = "zeze_design"
    
    def __init__(self, workspace_root: str = "."):
        super().__init__(workspace_root=workspace_root)
        self.workspace_root = os.path.realpath(os.path.abspath(workspace_root))
    
    async def _run_design_studio(self, task_id: str, description: str) -> Dict[str, Any]:
        """Tasarım Stüdyosu: VisualDirector → LayoutComposer / ParametricSculptor uzman pipeline'ı."""
        from core.ai.providers.visual_director import VisualDirector
        from core.ai.providers.layout_composer import LayoutComposer
        from core.ai.providers.parametric_sculptor import ParametricSculptor

        desc_lower = description.lower()
        director = VisualDirector()
        analysis = await director.analyze(description)

        results: Dict[str, Any] = {"visual_direction": analysis}

        # 3D / parametrik niyet
        if any(kw in desc_lower for kw in ["3d", "parametrik", "parametric", "model", "heykel", "sculpt"]):
            sculptor = ParametricSculptor()
            results["parametric"] = await sculptor.sculpt(analysis if isinstance(analysis, dict) else {"prompt": description})
        else:
            composer = LayoutComposer()
            results["layout"] = await composer.compose(analysis if isinstance(analysis, dict) else {"prompt": description})

        # Deliverable: stüdyo raporunu yaz
        report_dir = os.path.join(self.workspace_root, "departments", self.department, "reports", task_id)
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, "design_studio_output.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        output = (
            f"# Tasarım Stüdyosu Çıktısı\n\n"
            f"**Görev:** {description}\n\n"
            f"## Sanat Yönetimi\n{json.dumps(analysis, ensure_ascii=False, indent=2, default=str)[:800]}\n\n"
            f"**Üretilen artefakt:** `{report_path}`"
        )
        return {
            "success": True,
            "task_id": task_id,
            "output": output,
            "artifacts": [report_path],
            "deliverable": True,
        }

    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_id = self._safe_task_id(task_data)
        task_type = task_data.get("task_type", "general")
        description = task_data.get("description", "Detaylı bir analiz ve rapor hazırla.")

        self.logger.info(f"[{task_id}] Görev alındı: {description[:50]}...")
        await self.publish_live_event("Task_Start", "Processing", f"Tasarım görevi başlatıldı: {description[:50]}...")

        # Tasarım Stüdyosu niyeti (layout/görsel yön/3D) → uzman pipeline; React component değilse
        studio_keywords = ["layout", "düzen", "yerleşim", "moodboard", "sanat yön", "visual direction",
                           "3d", "parametrik", "parametric", "renk paleti", "kompozisyon"]
        component_keywords = ["component", "bileşen", "react", "tsx", "buton", "card", "dashboard"]
        if any(kw in description.lower() for kw in studio_keywords) and not any(kw in description.lower() for kw in component_keywords):
            self.logger.info(f"[{task_id}] Tasarım Stüdyosu niyeti → uzman pipeline çalıştırılıyor.")
            try:
                return await self._run_design_studio(task_id, description)
            except Exception as e:
                self.logger.error(f"[{task_id}] Stüdyo pipeline hatası: {e}. React akışına düşülüyor.")
        
        # Observability Trace Başlat
        trace = Trace(department=self.department, task_description=description)
        
        state_dir = os.path.join(self.workspace_root, "departments", self.department, "reports", task_id)
        os.makedirs(state_dir, exist_ok=True)
        
        # Geçmiş Hafızayı Çek (ZOM Kurumsal Hafıza)
        past_context = self.memory.recall_for_task(description)
        
        # Gerçek LLM Çağrısı (Dinamik Üretim + Tool Calling + Kurumsal Hafıza + Self Correction + Compile Check)
        system_prompt = (
            "Sen ZezeLabs Tasarım (Design) ve Arayüz Geliştirme (UI/UX) uzmanı otonom ajansın. "
            "Görevin, ZezeLabs Holding'in premium tasarım çizgilerine uygun React + Tailwind v4 component'leri tasarlamak ve yazmaktır.\n\n"
            "TASARIM VE KODLAMA İLKELERİ:\n"
            "1. Renkler: Browser varsayılanlarını reddet. HSL tabanlı renkler, neon cyan/violet detayları, slate-950 arka plan ve glassmorphism kullan.\n"
            "2. İkonlar: 'lucide-react' kütüphanesindeki ikonları kullan. İkonları React component gibi import et (örn: import { Sparkles } from 'lucide-react';).\n"
            "3. Animasyonlar: 'framer-motion' kütüphanesini kullanabilirsin.\n"
            "4. Dosya Yazma: Ürettiğin React componentlerini 'file_writer' yeteneğini kullanarak 'frontend/src/components/dynamic/{ComponentName}.tsx' yoluna kaydetmelisin. Dosya adı ve default export component adı birebir aynı olmalıdır.\n"
            "5. Kendini Düzeltme: Yazdığın kod otomatik olarak 'npx tsc --noEmit' derleme kontrolünden geçecektir. Eğer hata çıkarsa sana iletilecek hata loglarına göre kodunu düzeltip dosyayı tekrar yazmalısın."
        )
        if past_context:
            system_prompt += f"\n\nŞirket Geçmiş Hafızası:\n{past_context}"
            
        max_retries = 3
        llm_response = ""
        current_description = description
        
        for attempt in range(max_retries):
            await self.publish_live_event("LLM_Generation", "Processing", f"Arayüz bileşeni üretiliyor... (Deneme {attempt+1})")
            llm_response = await self.ask_llm_with_tools(prompt=current_description, system_prompt=system_prompt)
            
            # TypeScript compile-safety check execution using async subprocess (Vulnerability/Performance Fix 5)
            import asyncio
            frontend_path = os.path.realpath(os.path.join(self.workspace_root, "frontend"))
            cmd = ["npx.cmd", "tsc", "--noEmit"] if os.name == 'nt' else ["npx", "tsc", "--noEmit"]
            
            await self.publish_live_event("Compile_Check", "Processing", f"TypeScript derleme ve tip güvenliği kontrol ediliyor... (Deneme {attempt+1})")
            try:
                if os.name == 'nt':
                    # On Windows, we run via shell execution to support .cmd extension correctly
                    cmd_str = " ".join(cmd)
                    proc = await asyncio.create_subprocess_shell(
                        cmd_str,
                        cwd=frontend_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                else:
                    proc = await asyncio.create_subprocess_exec(
                        cmd[0], *cmd[1:],
                        cwd=frontend_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                
                try:
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=40)
                    stdout_str = stdout.decode('utf-8', errors='ignore')
                    stderr_str = stderr.decode('utf-8', errors='ignore')
                    returncode = proc.returncode
                except asyncio.TimeoutError:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                    raise Exception("tsc compile check timed out after 40 seconds")
                
                if returncode == 0:
                    self.logger.info(f"[{task_id}] tsc compile check succeeded on attempt {attempt+1}")
                    await self.publish_live_event("Compile_Check", "Success", f"TypeScript derleme kontrolü başarılı! (Deneme {attempt+1})")
                    break
                else:
                    compile_errors = stdout_str or stderr_str
                    self.logger.warning(f"[{task_id}] Compile errors detected on attempt {attempt+1}:\n{compile_errors[:300]}")
                    await self.publish_live_event("Compile_Check", "Warning", f"TypeScript derleme hatası! Kendi kendini iyileştirme döngüsü tetikleniyor... (Deneme {attempt+1})")
                    
                    # Feed compile errors back for self-healing iteration
                    current_description = (
                        description + 
                        f"\n\n[TYPESCRIPT DERLEME HATASI TESPİT EDİLDİ - DENEME {attempt+1}]\n"
                        f"Yazdığınız kod tsc derleyicisinde hata verdi. Lütfen hata loglarına göre kodunuzu düzeltin ve file_writer ile tekrar kaydedin:\n"
                        f"{compile_errors[:1000]}"
                    )
            except Exception as check_err:
                self.logger.error(f"[{task_id}] Failed to execute compile check: {check_err}")
                await self.publish_live_event("Compile_Check", "Warning", f"Derleme kontrolü çalıştırılamadı: {str(check_err)}")
                break
            
        # Token tahmini yap
        trace.estimate_tokens(description + llm_response)
        
        # Hafizaya Kaydet (Gelecek görevler için)
        self.memory.add_memory(memory_text=llm_response, metadata={"task": description, "dept": self.department}, tier="long")
        
        report = {
            "task_id": task_id,
            "department": self.department,
            "timestamp": datetime.now().isoformat(),
            "query": description,
            "output": llm_response,
            "status": "completed",
            "trace_id": trace.trace_id
        }
        
        report_path = os.path.join(state_dir, "report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        self.logger.info(f"[{task_id}] Rapor oluşturuldu: {report_path}")
        await self.publish_live_event("Task_Finished", "Success", "Tasarım görevi başarıyla tamamlandı, bileşen yayına hazır!")
        
        # Trace'i Kapat
        trace.finish(status="success")
        
        valid = self._validate_artifact(report_path)
        return {
            "success": True,
            "report_path": report_path,
            "task_id": task_id,
            "trace_id": trace.trace_id,
            "output": llm_response,
            "artifacts": [report_path],
            "deliverable": valid,
        }
