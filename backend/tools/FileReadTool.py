import os
import logging
from .base import Tool

log = logging.getLogger("jarvis.tools.file_read")

class FileReadTool(Tool):
    def __init__(self):
        super().__init__(
            name="file_read",
            description="Dosya icerigini okur.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        )

    def execute(self, **kwargs):
        path = kwargs.get("path")
        if not path or not os.path.exists(path): return f"HATA: Dosya bulunamadi: {path}"
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return "".join([f"{i+1}\t| {line}" for i, line in enumerate(lines)])
        except Exception as e: return f"HATA: {e}"
