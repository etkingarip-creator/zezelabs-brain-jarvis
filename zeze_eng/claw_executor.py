import subprocess
import os

class ClawExecutor:
    def __init__(self, workspace_dir: str):
        self.workspace_dir = workspace_dir
        # Docker ortamında Clawde_Code'un yolu
        self.clawde_path = "/app/Clawde_Code/dist/main.js"

    def execute(self, task_description: str) -> dict:
        print(f"[ClawExecutor] Node.js tabanlı Clawde_Code tetikleniyor...")
        
        # Görev metnini güvenli hale getir
        safe_task = task_description.replace('"', '\\"')
        
        # Komut: node /app/Clawde_Code/dist/main.js -p "görev"
        cmd = f'node {self.clawde_path} -p "{safe_task}"'
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=self.workspace_dir,
                capture_output=True,
                text=True
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
