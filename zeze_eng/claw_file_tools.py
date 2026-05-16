import os

class ClawFileTools:
    def __init__(self, workspace_dir: str):
        self.workspace_dir = os.path.abspath(workspace_dir)

    def _safe_path(self, filepath: str) -> str:
        """Dosya yolunun workspace dışına çıkmasını engeller (Path Traversal koruması)."""
        abs_path = os.path.abspath(os.path.join(self.workspace_dir, filepath))
        if not abs_path.startswith(self.workspace_dir):
            raise ValueError(f"Güvenlik İhlali: {filepath} çalışma dizini dışında.")
        return abs_path

    def read_file(self, filepath: str) -> str:
        path = self._safe_path(filepath)
        if not os.path.exists(path):
            return f"Hata: {filepath} bulunamadı."
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Okuma Hatası: {str(e)}"

    def write_file(self, filepath: str, content: str) -> str:
        path = self._safe_path(filepath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Başarılı: {filepath} yazıldı."
        except Exception as e:
            return f"Yazma Hatası: {str(e)}"

    def list_files(self, subdir: str = ".") -> str:
        path = self._safe_path(subdir)
        if not os.path.exists(path):
            return f"Hata: Dizin bulunamadı."
        files = []
        for root, _, filenames in os.walk(path):
            for file in filenames:
                rel_dir = os.path.relpath(root, self.workspace_dir)
                if rel_dir == ".":
                    files.append(file)
                else:
                    files.append(os.path.join(rel_dir, file).replace("\\", "/"))
        return "\n".join(files) if files else "Klasör boş."
