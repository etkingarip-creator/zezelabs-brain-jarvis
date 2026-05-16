import os
import logging
from .base import Tool

log = logging.getLogger("jarvis.tools.file_edit")

class FileEditTool(Tool):
    def __init__(self):
        super().__init__(
            name="file_edit",
            description="Dosya icinde hassas metin degisimi yapar.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old_string": {"type": "string"},
                    "new_string": {"type": "string"},
                    "replace_all": {"type": "boolean"}
                },
                "required": ["path", "old_string", "new_string"]
            }
        )

    def execute(self, **kwargs):
        path = kwargs.get("path")
        old_string = kwargs.get("old_string")
        new_string = kwargs.get("new_string")
        replace_all = kwargs.get("replace_all", False)
        
        if not path or not old_string or new_string is None:
            return "HATA: Gecersiz parametreler (path, old_string veya new_string eksik)."
        
        if not os.path.exists(path): return f"HATA: Dosya bulunamadi: {path}"
        
        try:
            with open(path, 'r', encoding='utf-8') as f: content = f.read()
            if old_string not in content: return f"HATA: '{old_string}' bulunamadi."
            
            if replace_all: new_content = content.replace(old_string, new_string)
            else: new_content = content.replace(old_string, new_string, 1)
            
            with open(path, 'w', encoding='utf-8') as f: f.write(new_content)
            return f"BASARI: {path} guncellendi."
        except Exception as e: return f"HATA: {e}"
