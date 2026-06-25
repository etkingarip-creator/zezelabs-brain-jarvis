"""
Zezelabs Holding OS - ZezeCommsAgent
Gerçek içerik üretimi: Copywriter (içerik) + SEOOptimizer + dosyaya yazma.
Deneme yazmaz; gerçek içerik dosyaları üretir ve diske teslim eder.
"""
import os
import json
from typing import Dict, Any
from datetime import datetime
from core.operator_runtime.base_agent import BaseDepartmentAgent


class ZezeCommsAgent(BaseDepartmentAgent):
    department = "zeze_comms"

    def __init__(self, workspace_root: str = "."):
        super().__init__(workspace_root=workspace_root)
        self.workspace_root = os.path.realpath(os.path.abspath(workspace_root))

    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_id = self._safe_task_id(task_data)
        description = task_data.get("description", "") or ""

        from core.skills.registry import SkillRegistry
        registry = SkillRegistry()

        # 1. Copywriter: gerçek içerik üret (SEO başlık + meta + gövde)
        writer_prompt = (
            f"GÖREV: {description}\n\n"
            f"Profesyonel bir iletişim/içerik uzmanı olarak yayına HAZIR içerik üret.\n"
            f"Ton: güvenilir, net, otoriter. SEO uyumlu başlık ve meta açıklama ekle.\n"
            f"Markdown formatında, '# Başlık' ile başla, meta açıklamayı '> ' ile ver."
        )
        system_prompt = "Sen ZezeLabs İletişim ajanısın. PR metinleri, duyurular, e-postalar ve SEO uyumlu içerik üretirsin. Yer tutucu bırakmazsın, içerik yayına hazırdır."
        content = await self.ask_llm(writer_prompt, system_prompt=system_prompt)

        # 2. Deliverable: içerik dosyasını gerçekten yaz (file_writer)
        rel_dir = os.path.relpath(
            os.path.join(self.workspace_root, "departments", self.department, "reports", task_id),
            os.getcwd()
        ).replace("\\", "/")
        content_path = f"{rel_dir}/content.md"
        await registry.execute_tool("file_writer", {"file_path": content_path, "content": content})

        # Meta JSON da yaz
        meta = {
            "task_id": task_id,
            "department": self.department,
            "timestamp": datetime.now().isoformat(),
            "query": description,
            "content_file": content_path,
            "char_count": len(content),
        }
        report_dir = os.path.join(self.workspace_root, "departments", self.department, "reports", task_id)
        os.makedirs(report_dir, exist_ok=True)
        with open(os.path.join(report_dir, "comms_meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

        output = (
            f"# İletişim — İçerik Teslimi\n\n"
            f"**Görev:** {description}\n"
            f"**Üretilen dosya:** `{content_path}` ({len(content)} karakter)\n\n"
            f"---\n\n{content[:600]}..."
        )
        return {
            "success": True,
            "task_id": task_id,
            "output": output,
            "artifacts": [content_path],
            "deliverable": True,
        }
