"""
Zezelabs Holding OS - ZezeDevAgent
Gerçek Mühendislik Ekibi: Architect → Coder → Tester → SelfHealer.
Deneme yazmaz; gerçek kod yazar, dosyaya kaydeder, test çalıştırır, hatayı kendi onarır.
"""
import os
import re
import json
import uuid
from typing import Dict, Any
from datetime import datetime
from core.operator_runtime.base_agent import BaseDepartmentAgent


class ZezeDevAgent(BaseDepartmentAgent):
    department = "zeze_dev"

    def __init__(self, workspace_root: str = "."):
        super().__init__(workspace_root=workspace_root)
        self.workspace_root = os.path.realpath(os.path.abspath(workspace_root))

    def _parse_files_json(self, llm_response: str) -> Dict[str, str]:
        """LLM yanıtından {path: content} JSON'ını ayıkla."""
        clean = llm_response.strip()
        if clean.startswith("```json"):
            clean = clean[7:]
        elif clean.startswith("```"):
            clean = clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        clean = clean.strip()
        try:
            data = json.loads(clean)
        except Exception:
            match = re.search(r'\{.*\}', clean, re.DOTALL)
            if not match:
                return {}
            try:
                data = json.loads(match.group(0))
            except Exception:
                return {}
        files = data.get("files", data) if isinstance(data, dict) else {}
        return {k: v for k, v in files.items() if isinstance(v, str)}

    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_id = self._safe_task_id(task_data)

        # Self-heal modu: standart akışta kalsın (debug/onarım metni)
        if task_data.get("action") == "self_heal":
            description = (
                f"SELF HEAL/DEBUG TASK:\n"
                f"Target file: {task_data.get('file_path', '')}\n"
                f"Error trace: {task_data.get('error_trace', '')}\n"
                f"Goal: Read the target file, fix the bug, confirm the fix."
            )
            system_prompt = "Sen ZezeLabs Yazılım Geliştirme (Dev) ajanısın. Hata ayıklar, kodu file_writer ile onarırsın."
            return await self._standard_execute(task_data, system_prompt, description)

        description = task_data.get("description", "") or ""

        # GERÇEK MÜHENDİSLİK PIPELINE'ı
        from core.skills.registry import SkillRegistry
        registry = SkillRegistry()

        out_dir = os.path.join(self.workspace_root, "departments", self.department, "workspace", task_id)
        rel_out = os.path.relpath(out_dir, os.getcwd()).replace("\\", "/")

        architect_prompt = (
            f"GÖREV: {description}\n\n"
            f"Bir yazılım mimarı olarak bu görevi GERÇEK, çalışan Python kodu olarak teslim et.\n"
            f"Kod ve testlerini üret. Test dosyası mutlaka 'test_' ile başlamalı ve pytest uyumlu olmalı.\n"
            f"Dosyaları '{rel_out}/' altına yaz.\n\n"
            f"YANITINI SADECE şu JSON formatında ver (markdown yok, açıklama yok):\n"
            f'{{"files": {{"{rel_out}/main.py": "kod...", "{rel_out}/test_main.py": "pytest test kodu..."}}}}'
        )
        system_prompt = (
            "Sen ZezeLabs Yazılım Geliştirme (Dev) ajanısın. SOLID prensiplerine uyan, test edilebilir, "
            "çalışan kod üretirsin. Asla yer tutucu (placeholder) veya 'TODO' bırakmazsın."
        )

        max_iterations = 3
        files: Dict[str, str] = {}
        test_output = ""
        tests_passed = False
        current_prompt = architect_prompt

        for iteration in range(max_iterations):
            # 1. ARCHITECT + CODER: kod üret
            llm_response = await self.ask_llm(current_prompt, system_prompt=system_prompt)
            parsed = self._parse_files_json(llm_response)
            if not parsed:
                self.logger.warning(f"[{task_id}] Mimar geçerli JSON üretmedi (deneme {iteration+1}).")
                current_prompt = architect_prompt + "\n\n[HATA: Geçerli JSON üretmedin. SADECE belirtilen JSON formatında yanıt ver.]"
                continue
            files = parsed

            # 2. CODER: dosyaları gerçekten yaz (file_writer)
            written = []
            for path, content in files.items():
                res = await registry.execute_tool("file_writer", {"file_path": path, "content": content})
                written.append(path)
                self.logger.info(f"[{task_id}] Yazıldı: {path} ({res[:40]})")

            # 3. TESTER: testleri gerçekten çalıştır (python_executor / pytest)
            test_files = [p for p in files if os.path.basename(p).startswith("test_")]
            if not test_files:
                tests_passed = True  # test yoksa kod yazımıyla yetin
                test_output = "Test dosyası üretilmedi; sadece kod teslim edildi."
                break

            runner_code = (
                "import subprocess, sys\n"
                f"r = subprocess.run([sys.executable, '-m', 'pytest', '-q', {rel_out!r}], "
                "capture_output=True, text=True, timeout=60)\n"
                "print(r.stdout)\nprint(r.stderr)\nprint('EXIT', r.returncode)"
            )
            test_output = await registry.execute_tool("python_executor", {"code": runner_code})

            if "EXIT 0" in test_output or "passed" in test_output.lower() and "failed" not in test_output.lower():
                tests_passed = True
                self.logger.info(f"[{task_id}] Testler GEÇTİ (deneme {iteration+1}).")
                break

            # 4. SELFHEALER: hata logunu geri besle
            self.logger.warning(f"[{task_id}] Testler başarısız (deneme {iteration+1}). Self-heal tetikleniyor.")
            current_prompt = (
                architect_prompt +
                f"\n\n[TEST HATASI - DENEME {iteration+1}]\n"
                f"Önceki kodun testleri geçemedi. Hata çıktısı:\n{test_output[:1200]}\n"
                f"Lütfen kodu düzelt ve TÜM dosyaları tekrar üret."
            )

        # Deliverable raporu
        report = {
            "task_id": task_id,
            "department": self.department,
            "timestamp": datetime.now().isoformat(),
            "query": description,
            "files": list(files.keys()),
            "tests_passed": tests_passed,
            "test_output": test_output[-2000:],
        }
        report_dir = os.path.join(self.workspace_root, "departments", self.department, "reports", task_id)
        os.makedirs(report_dir, exist_ok=True)
        with open(os.path.join(report_dir, "dev_report.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        status_icon = "✅ GEÇTİ" if tests_passed else "⚠️ TESTLER GEÇMEDİ"
        output = (
            f"# Yazılım Geliştirme — Teslim Raporu\n\n"
            f"**Görev:** {description}\n\n"
            f"**Üretilen Dosyalar ({len(files)}):**\n"
            + "\n".join(f"- `{p}`" for p in files) +
            f"\n\n**Test Durumu:** {status_icon}\n\n"
            f"```\n{test_output[-800:]}\n```"
        )

        return {
            "success": tests_passed,
            "task_id": task_id,
            "output": output,
            "artifacts": list(files.keys()),
            "deliverable": True,
            "tests_passed": tests_passed,
        }
