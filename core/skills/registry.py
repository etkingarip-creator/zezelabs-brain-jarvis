import os
import importlib
import inspect

class BaseSkill:
    """Tüm dinamik yetenekler için temel sınıf (SuperAGI/AutoGPT tarzı)."""
    name = "base_skill"
    description = "Temel yetenek"
    parameters = {}  # JSON Schema formatında parametre tanımları

    async def execute(self, **kwargs) -> str:
        raise NotImplementedError

class SkillRegistry:
    """Ajanlara dinamik olarak yetenek (tool) yükleyen Market (Registry)."""
    
    def __init__(self):
        self.skills = {}
        self._load_skills()
        self._gate_clawde_skills()

    @staticmethod
    def _clawde_operational() -> bool:
        """Clawde köprüsü gerçekten çalışır durumda mı? (derlenmiş CLI veya açık bayrak)"""
        if os.getenv("CLAWDE_OPERATIONAL") == "1":
            return True
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        for cli in (root / "clawde_code" / "dist" / "index.js",
                    root / "Clawde_Code" / "dist" / "index.js"):
            if cli.exists():
                return True
        return False

    def _gate_clawde_skills(self):
        """Sağlık kapısı (kalıcı çözüm): Clawde köprüsü operasyonel DEĞİLSE clawde_*
        skill'lerini kayıttan düşür — LLM'e çağrılınca çöken sahte kapasite sunulmaz.
        Köprü çalışır hale gelince (dist build veya CLAWDE_OPERATIONAL=1) otomatik aktifleşir."""
        clawde = [n for n in self.skills if n.startswith("clawde_")]
        if not clawde:
            return
        if self._clawde_operational():
            print(f"[SkillRegistry] Clawde bridge operational: {len(clawde)} clawde skills active.")
            return
        for n in clawde:
            del self.skills[n]
        print(
            f"[SkillRegistry] WARNING: Clawde bridge not operational -> {len(clawde)} clawde "
            f"skills disabled (fake capability prevented). Enable: build dist + CLAWDE_OPERATIONAL=1"
        )

    def _load_skills(self):
        skills_dir = os.path.dirname(os.path.abspath(__file__))
        for filename in os.listdir(skills_dir):
            if filename.endswith(".py") and filename not in ["__init__.py", "registry.py"]:
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(f"core.skills.{module_name}")
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, BaseSkill) and obj is not BaseSkill:
                            skill_instance = obj()
                            self.skills[skill_instance.name] = skill_instance
                            print(f"[SkillRegistry] Loaded skill: {skill_instance.name}")
                except Exception as e:
                    print(f"[SkillRegistry] Error loading skill {filename}: {e}")

    def get_all_tools_schema(self) -> list:
        """OpenRouter/OpenAI tool formatında tüm yetenekleri döndürür."""
        tools = []
        for name, skill in self.skills.items():
            tools.append({
                "type": "function",
                "function": {
                    "name": skill.name,
                    "description": skill.description,
                    "parameters": skill.parameters
                }
            })
        return tools

    async def execute_tool(self, name: str, kwargs: dict) -> str:
        """Bir yeteneği çalıştırır."""
        if name in self.skills:
            try:
                result = await self.skills[name].execute(**kwargs)
                return str(result)
            except Exception as e:
                return f"Error executing {name}: {str(e)}"
        return f"Tool {name} not found."
