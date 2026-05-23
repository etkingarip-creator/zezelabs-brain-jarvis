import os
import sys
import subprocess
import httpx
import logging
import webbrowser
from typing import Optional

log = logging.getLogger("backend_launcher")

class BackendLauncher:
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.host = os.getenv("ZOM_DESKTOP_BACKEND_HOST", "127.0.0.1")
        self.port = os.getenv("ZOM_DESKTOP_BACKEND_PORT", "5000")

    def build_command(self) -> list[str]:
        # Safe default overrides
        return [
            sys.executable, "-m", "uvicorn", 
            "backend.jarvis:app", 
            "--host", self.host, 
            "--port", self.port
        ]

    def start_backend(self) -> dict:
        if self.process and self.process.poll() is None:
            return {"status": "error", "message": "Backend already running"}
            
        env = os.environ.copy()
        env["ZOM_ENABLE_AUTO_GITHUB_PUSH"] = "false"
        env["ZOM_ENABLE_VOICE_LISTENER"] = "false"
        env["ZOM_ENABLE_LEGACY_OPENCLAW_CLEANUP"] = "false"
        env["ZOM_ENABLE_HERMES_GATEWAY"] = "false"
        env["ZOM_ENABLE_OLLAMA_FALLBACK"] = "false"

        try:
            # Using list args, no shell=True
            self.process = subprocess.Popen(
                self.build_command(),
                env=env,
                stdout=subprocess.DEVNULL, # We keep it clean
                stderr=subprocess.DEVNULL,
                creationflags=0x08000000 if sys.platform == "win32" else 0
            )
            return {"status": "success", "message": "Backend started"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def stop_backend(self) -> dict:
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
            return {"status": "success", "message": "Backend stopped"}
        return {"status": "error", "message": "Backend not running"}

    def health_check(self) -> dict:
        try:
            resp = httpx.get(f"http://{self.host}:{self.port}/api/runtime/status", timeout=2)
            if resp.status_code == 200:
                return {"status": "online", "data": resp.json()}
        except Exception:
            pass
        return {"status": "offline"}

    def open_browser_dashboard(self) -> dict:
        webbrowser.open(f"http://{self.host}:{self.port}/docs")
        return {"status": "success"}
