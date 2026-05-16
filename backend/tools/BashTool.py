import subprocess
import logging
from .base import Tool

log = logging.getLogger("jarvis.tools.bash")

class BashTool(Tool):
    def __init__(self):
        super().__init__(
            name="bash",
            description="Terminalde komut calistirir.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string"}
                },
                "required": ["command"]
            }
        )

    def execute(self, **kwargs):
        command = kwargs.get("command")
        if not command: return "HATA: Komut belirtilmedi."
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return (result.stdout + "\n" + result.stderr).strip() or "Komut calisti."
        except Exception as e: return f"HATA: {e}"
