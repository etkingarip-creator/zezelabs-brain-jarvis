import os
import json

class ProjectScanner:
    """
    Jarvis'in harici projeleri tarama ve mimari analiz yapma yeteneği.
    Antigravity'nin 'manifestly' projesinde yaptığı tarama mantığını otonomlaştırır.
    """
    def __init__(self):
        self.ignore_dirs = [".git", "node_modules", "venv", ".expo", "android", "ios"]

    def scan_directory(self, path):
        """Dizini tarar ve dosya yapısını analiz eder."""
        print(f"[ProjectScanner] 🔍 Proje Taranıyor: {path}")
        structure = []
        try:
            for root, dirs, files in os.walk(path):
                # Ignore noisy directories
                dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
                
                level = root.replace(path, "").count(os.sep)
                indent = " " * 4 * level
                print(f"{indent}{os.path.basename(root)}/")
                
                for f in files:
                    structure.append(os.path.join(root, f))
            
            return {
                "status": "SUCCESS",
                "file_count": len(structure),
                "structure_preview": structure[:20] # Özet
            }
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    def detect_tech_stack(self, path):
        """Projenin teknolojisini (React Native, Python, Go vb.) tespit eder."""
        # package.json varsa Node/React/RN
        # requirements.txt varsa Python
        # go.mod varsa Go
        pass

scanner = ProjectScanner()
