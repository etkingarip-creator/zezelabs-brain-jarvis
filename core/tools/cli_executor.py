import subprocess
import os

class SandboxCLIExecutor:
    """
    ZOM v4 Autonomous CLI Executor.
    ZOM Doktrini uyarinca ajanin calistirdigi komutlar KESINLIKLE dev_workspace disina cikamaz.
    """
    def __init__(self, workspace_path: str):
        self.workspace_path = os.path.abspath(workspace_path)
        os.makedirs(self.workspace_path, exist_ok=True)
        
    def execute(self, command: str, timeout_seconds: int = 30) -> dict:
        """
        Komutu sandbox (dev_workspace) icinde calistirir.
        Zaman asimi (timeout) korumasi saglar.
        """
        # Guardrail: Dizin degistirme hilelerine karsi basit koruma
        forbidden_patterns = ["cd ..", "cd /", "rm -rf /"]
        for pattern in forbidden_patterns:
            if pattern in command:
                return {
                    "success": False, 
                    "error": f"ZOM SECURITY GUARDRAIL: '{pattern}' komutu yasaktir. Sadece proje klasorunde calisabilirsiniz."
                }

        print(f"[SandboxCLI] Komut calistiriliyor: {command}")
        try:
            result = subprocess.run(
                command,
                cwd=self.workspace_path,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )
            
            output_str = result.stdout.strip()
            error_str = result.stderr.strip()
            
            # Ciktilar cok uzunsa kirp (Token tasarrufu)
            if len(output_str) > 2000:
                output_str = output_str[:2000] + "\n...[TRUNCATED BY ZOM]..."
            if len(error_str) > 2000:
                error_str = error_str[:2000] + "\n...[TRUNCATED BY ZOM]..."

            return {
                "success": result.returncode == 0,
                "stdout": output_str,
                "stderr": error_str,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Zaman asimi: Komut {timeout_seconds} saniye icinde tamamlanamadi."}
        except Exception as e:
            return {"success": False, "error": str(e)}
