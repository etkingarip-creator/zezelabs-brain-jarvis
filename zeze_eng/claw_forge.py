import os
import subprocess
from core.tools.cli_executor import SandboxCLIExecutor

class ClawForge:
    def __init__(self, workspace_dir: str):
        self.workspace_dir = workspace_dir
        self.cli = SandboxCLIExecutor(workspace_dir)

    def forge(self, task_description: str) -> dict:
        print(f"[Claw-Forge] Otonom inşaa başlatılıyor: {self.workspace_dir}")
        safe_task = task_description.replace('"', '\\"')
        
        # Sadece workspace içinde claude komutu çalıştır. --yes ile onaysız.
        claude_cmd = f'claude -p "{safe_task} --yes"'
        
        result = self.cli.execute(claude_cmd)
        
        if result["success"]:
            print("[Claw-Forge] ✅ Claude Code görevini başarıyla tamamladı.")
        else:
            print(f"[Claw-Forge] ⚠️ Hata:\n{result['stderr']}")
            
        return result
