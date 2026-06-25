"""
Zezelabs Holding OS - AppFactoryAgent
Gerçek LLM Entegrasyonlu Ajan
"""
import os
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
from core.operator_runtime.base_agent import BaseDepartmentAgent
from core.observability.tracer import Trace
from core.operator_runtime.contracts import AgentResult, DepartmentName
from core.operator_runtime.telemetry import get_telemetry

class AppFactoryAgent(BaseDepartmentAgent):
    department = "app_factory"
    
    def __init__(self, workspace_root: str = "."):
        super().__init__(workspace_root=workspace_root)
        self.workspace_root = os.path.realpath(os.path.abspath(workspace_root))
    
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        # Görev-tipi kapsama: scaffold | spec/feature | aksi → generic (needs_review)
        routes = [
            (["scaffold", "iskelet", "uygulama yap", "uygulama oluştur", "app yap",
              "proje oluştur", "kod üret", "mvp", "fastapi", "react", "web uygulama",
              "saas", "api oluştur", "build app", "create app", "generate app"],
             self._handle_scaffold),
            (["spec", "spesifikasyon", "feature", "özellik listesi", "user flow",
              "kullanıcı akış", "teknik doküman", "gereksinim", "requirement"],
             self._handle_spec),
        ]
        default_sp = "Sen ZezeLabs Uygulama Fabrikası ajanısın. Uygulama konseptleri, user flow şemaları, MVP feature listeleri ve teknik spec üretirsin."
        return await self.dispatch_by_task_type(task_data, routes, default_sp)

    async def _handle_scaffold(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        description = task_data.get("description", "") or ""
        self.logger.info("[app_factory] Scaffold handler → run_dry_task.")
        task_id = self._safe_task_id(task_data)
        agent_result = await self.run_dry_task(goal=description, task_id=task_id)
        scaffold_dir = os.path.join(self.workspace_root, "app_factory", "scaffolds", task_id)
        files_written = [
            os.path.join(scaffold_dir, tr.get("relative"))
            for tr in (agent_result.tool_results or [])
        ]
        valid = all(self._validate_artifact(f) for f in files_written) if files_written else False
        output = (
            f"# App Factory — Scaffold Tamamlandı\n\n**Hedef:** {description}\n\n"
            f"**Üretilen Dosyalar ({len(files_written)}):**\n"
            + "\n".join(f"- `{f}`" for f in files_written)
        )
        return {
            "success": agent_result.success and valid,
            "task_id": task_id, "output": output,
            "artifacts": files_written, "deliverable": valid,
        }

    async def _handle_spec(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        import re
        description = task_data.get("description", "") or ""
        task_id = self._safe_task_id(task_data)
        prompt = (
            f"GÖREV: {description}\n\nBir ürün mimarı olarak yapılandırılmış teknik spesifikasyon üret.\n"
            f"SADECE şu JSON: {{\"app_name\":\"\",\"features\":[\"f1\"],\"user_flows\":[\"adım1\"],"
            f"\"tech_stack\":[\"\"],\"mvp_scope\":[\"\"],\"apis\":[{{\"endpoint\":\"\",\"method\":\"\"}}]}}"
        )
        resp = await self.ask_llm(prompt, system_prompt="Sen ZezeLabs ürün mimarısın. Uygulanabilir teknik spec üretirsin.")
        spec = {}
        try:
            m = re.search(r'\{.*\}', resp, re.DOTALL)
            if m: spec = json.loads(m.group(0))
        except Exception:
            spec = {"app_name": "N/A", "features": [resp[:200]]}
        report_dir = os.path.join(self.workspace_root, "departments", self.department, "reports", task_id)
        os.makedirs(report_dir, exist_ok=True)
        path = os.path.join(report_dir, "app_spec.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
        valid = self._validate_artifact(path)
        output = (
            f"# Teknik Spesifikasyon: {spec.get('app_name','N/A')}\n"
            f"- **Özellikler:** {', '.join(str(x) for x in spec.get('features', []))}\n"
            f"- **Tech Stack:** {', '.join(str(x) for x in spec.get('tech_stack', []))}\n"
            f"- **MVP:** {', '.join(str(x) for x in spec.get('mvp_scope', []))}"
        )
        return {"success": valid, "task_id": task_id, "output": output,
                "artifacts": [path], "deliverable": valid}

    async def run_dry_task(self, goal: str, task_id: Optional[str] = None) -> AgentResult:
        """
        Executes a dry-run scaffolding task using LLM dynamic code generation.
        Creates README.md, manifest.json, app/main.py, and tests/test_smoke.py.
        """
        import uuid
        import shutil
        
        if not task_id:
            task_id = str(uuid.uuid4())
            
        self.current_task_id = task_id
        self.logger.info(f"[{task_id}] Dry-run scaffolding started for goal: {goal}")
        
        scaffold_dir = os.path.realpath(os.path.abspath(os.path.join(self.workspace_root, "app_factory", "scaffolds", task_id)))
        os.makedirs(scaffold_dir, exist_ok=True)
        
        prompt = (
            f"Yeni bir uygulama şablonu (scaffold) oluşturmamız gerekiyor.\n"
            f"Hedef/Açıklama: {goal}\n\n"
            f"Senden aşağıdaki 4 dosyayı üretmeni rica ediyorum:\n"
            f"1. README.md: Projenin açıklaması, kurulum ve çalıştırma yönergeleri.\n"
            f"2. manifest.json: Projenin metaverileri (isim, sürüm, bağımlılıklar).\n"
            f"3. app/main.py: FastAPI veya benzeri bir framework ile yazılmış ana uygulama kodu.\n"
            f"4. tests/test_smoke.py: Uygulamanın düzgün çalışıp çalışmadığını kontrol eden basit bir test.\n\n"
            f"Lütfen yanıtı SADECE aşağıdaki JSON formatında döndür. Markdown kod blokları veya açıklama ekleme, sadece saf JSON:\n"
            f"{{\n"
            f"  \"README.md\": \"dosya içeriği buraya\",\n"
            f"  \"manifest.json\": \"dosya içeriği buraya\",\n"
            f"  \"app/main.py\": \"dosya içeriği buraya\",\n"
            f"  \"tests/test_smoke.py\": \"dosya içeriği buraya\"\n"
            f"}}\n"
        )
        
        # Direct async execution of ask_llm
        llm_response = ""
        try:
            llm_response = await self.ask_llm(prompt, system_prompt="Sen otonom bir yazılım mimarısın.")
        except Exception as e:
            self.logger.warning(f"LLM generation failed: {e}. Falling back to default templates.")
            
        files = {}
        if llm_response:
            try:
                clean_response = llm_response.strip()
                if clean_response.startswith("```json"):
                    clean_response = clean_response[7:]
                if clean_response.endswith("```"):
                    clean_response = clean_response[:-3]
                clean_response = clean_response.strip()
                files = json.loads(clean_response)
            except Exception as e:
                self.logger.warning(f"Failed to parse JSON response: {e}. Using templates.")
                
        required_files = ["README.md", "manifest.json", "app/main.py", "tests/test_smoke.py"]
        for rf in required_files:
            if rf not in files or not isinstance(files[rf], str) or len(files[rf].strip()) == 0:
                files[rf] = self._get_fallback_template(rf, goal)
                
        tool_results = []
        for rel_path, content in files.items():
            # Code validation syntax check before saving
            if not self._validate_code_syntax(rel_path, content):
                self.logger.warning(f"Generated file {rel_path} failed syntax check. Reverting to fallback template.")
                content = self._get_fallback_template(rel_path, goal)
                
            abs_path = os.path.join(scaffold_dir, rel_path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
            tool_results.append({
                "relative": rel_path.replace("\\", "/"),
                "content": content
            })
            
        # Record Telemetry Event
        try:
            get_telemetry().record_execution(
                task_id=task_id,
                department=self.department,
                tool_name="app_factory_dry_run",
                action="dry_run",
                status="success"
            )
        except Exception as e:
            self.logger.error(f"Failed to record telemetry: {e}")
            
        self.logger.info(f"[{task_id}] Scaffold generated successfully in {scaffold_dir}")
        
        return AgentResult(
            task_id=task_id,
            department=DepartmentName.APP_FACTORY,
            success=True,
            output=f"Scaffold successfully created for goal: {goal}",
            tool_results=tool_results
        )

    def _validate_code_syntax(self, filename: str, content: str) -> bool:
        """Validates syntax of generated files (Python, JSON, etc.) before saving."""
        if filename.endswith(".py"):
            try:
                compile(content, filename, "exec")
                return True
            except SyntaxError as se:
                self.logger.error(f"Syntax validation failed for Python file {filename}: {se}")
                return False
        elif filename.endswith(".json"):
            try:
                json.loads(content)
                return True
            except ValueError as ve:
                self.logger.error(f"Syntax validation failed for JSON file {filename}: {ve}")
                return False
        return True

    def _get_fallback_template(self, filename: str, goal: str) -> str:
        """Returns default high-quality file contents for scaffolding fallback based on goal keywords."""
        goal_lower = goal.lower()
        
        # Determine language/stack:
        is_react = "react" in goal_lower or "nextjs" in goal_lower or "frontend" in goal_lower
        is_go = "go" in goal_lower or "golang" in goal_lower
        
        if is_react:
            if filename == "README.md":
                return (
                    f"# React Scaffold: {goal}\n\n"
                    f"Generated by ZezeLabs AppFactory React templates.\n\n"
                    f"## Setup\n"
                    f"1. Run package installation.\n"
                    f"2. Launch python static server to host files.\n"
                )
            elif filename == "manifest.json":
                return json.dumps({
                    "name": "react-scaffold-app",
                    "version": "1.0.0",
                    "framework": "React / Next.js",
                    "description": f"React dashboard for: {goal}",
                    "dependencies": {
                        "react": "^18.2.0",
                        "react-dom": "^18.2.0"
                    }
                }, indent=2)
            elif filename == "app/main.py":
                return (
                    f"# React server and component bundle\n"
                    f"from fastapi import FastAPI\n"
                    f"from fastapi.responses import HTMLResponse\n\n"
                    f"app = FastAPI(title='React App Server')\n\n"
                    f"REACT_COMPONENT = '''\n"
                    f"function Dashboard() {{\n"
                    f"    return (\n"
                    f"        <div className='p-6 max-w-lg mx-auto bg-white rounded-xl shadow-md space-y-4'>\n"
                    f"            <h1 className='text-2xl font-bold text-gray-900'>{goal} Dashboard</h1>\n"
                    f"            <p className='text-gray-500'>Otonom üretilmiş React arayüzü.</p>\n"
                    f"        </div>\n"
                    f"    );\n"
                    f"}}\n"
                    f"'''\n\n"
                    f"@app.get('/', response_class=HTMLResponse)\n"
                    f"def read_root():\n"
                    f"    return f'<html><body><div id=\"root\"></div><script>{{REACT_COMPONENT}}</script></body></html>'\n"
                )
            elif filename == "tests/test_smoke.py":
                return (
                    f"from fastapi.testclient import TestClient\n"
                    f"from app.main import app\n\n"
                    f"client = TestClient(app)\n\n"
                    f"def test_react_server():\n"
                    f"    response = client.get('/')\n"
                    f"    assert response.status_code == 200\n"
                    f"    assert 'REACT_COMPONENT' not in response.text  # serves html\n"
                )
        elif is_go:
            if filename == "README.md":
                return (
                    f"# Go Scaffold: {goal}\n\n"
                    f"Generated by ZezeLabs AppFactory Go templates.\n\n"
                    f"## Setup\n"
                    f"1. Run go build.\n"
                )
            elif filename == "manifest.json":
                return json.dumps({
                    "name": "go-scaffold-app",
                    "version": "1.0.0",
                    "framework": "Go / Gin",
                    "description": f"Go microservice for: {goal}",
                    "dependencies": {
                        "gin": "v1.9.1"
                    }
                }, indent=2)
            elif filename == "app/main.py":
                return (
                    f"# Go API Server simulation in python\n"
                    f"# Real Go file contents are embed below:\n"
                    f"# package main; import 'fmt'; func main() {{ fmt.Println('{goal}') }}\n\n"
                    f"from fastapi import FastAPI\n"
                    f"app = FastAPI(title='Go Microservice Agent')\n"
                    f"@app.get('/')\n"
                    f"def get_status():\n"
                    f"    return {{'status': 'online', 'language': 'go', 'goal': {goal!r}}}\n"
                )
            elif filename == "tests/test_smoke.py":
                return (
                    f"from fastapi.testclient import TestClient\n"
                    f"from app.main import app\n\n"
                    f"client = TestClient(app)\n\n"
                    f"def test_go_service():\n"
                    f"    response = client.get('/')\n"
                    f"    assert response.status_code == 200\n"
                    f"    assert response.json()['language'] == 'go'\n"
                )
        
        # Default FastAPI (Python) Fallback
        if filename == "README.md":
            return (
                f"# Scaffold: {goal}\n\n"
                f"Generated automatically by ZezeLabs AppFactory.\n\n"
                f"## Kurulum ve Çalıştırma\n\n"
                f"1. Bağımlılıkları yükleyin:\n"
                f"```bash\n"
                f"pip install -r requirements.txt\n"
                f"```\n"
                f"2. Uygulamayı başlatın:\n"
                f"```bash\n"
                f"python -m app.main\n"
                f"```\n"
            )
        elif filename == "manifest.json":
            return json.dumps({
                "name": "scaffold-app",
                "version": "1.0.0",
                "description": f"Generated automatically for: {goal}",
                "dependencies": {
                    "fastapi": ">=0.104.0",
                    "uvicorn": ">=0.24.0"
                }
            }, indent=2)
        elif filename == "app/main.py":
            return (
                f"from fastapi import FastAPI\n\n"
                f"app = FastAPI(title='Scaffold App')\n\n"
                f"@app.get('/')\n"
                f"def read_root():\n"
                f"    return {{'message': 'Hello World', 'goal': {goal!r}}}\n"
            )
        elif filename == "tests/test_smoke.py":
            return (
                f"from fastapi.testclient import TestClient\n"
                f"from app.main import app\n\n"
                f"client = TestClient(app)\n\n"
                f"def test_read_root():\n"
                f"    response = client.get('/')\n"
                f"    assert response.status_code == 200\n"
                f"    assert response.json() == {{'message': 'Hello World', 'goal': {goal!r}}}\n"
            )
        return ""

    async def run_cycle(self) -> Dict[str, Any]:
        """
        Periodic self-execution.
        Scans 'app_factory/scaffolds/' and prunes old UUID directories.
        """
        import shutil
        self.logger.info("AppFactoryAgent: Starting periodic cycle / garbage collection.")
        
        scaffolds_dir = os.path.realpath(os.path.abspath(os.path.join(self.workspace_root, "app_factory", "scaffolds")))
        if not os.path.exists(scaffolds_dir):
            return {"status": "noop", "cleaned_dirs": 0}
            
        now = time.time()
        one_day_ago = now - 24 * 3600
        
        entries = []
        for name in os.listdir(scaffolds_dir):
            path = os.path.join(scaffolds_dir, name)
            if os.path.isdir(path):
                try:
                    mtime = os.path.getmtime(path)
                    entries.append((path, mtime))
                except Exception:
                    pass
                    
        cleaned_count = 0
        remaining_entries = []
        
        # Rule 1: Delete older than 24 hours
        for path, mtime in entries:
            if mtime < one_day_ago:
                try:
                    shutil.rmtree(path)
                    self.logger.info(f"Garbage collector: Deleted stale scaffold older than 24h: {path}")
                    cleaned_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to delete directory {path}: {e}")
            else:
                remaining_entries.append((path, mtime))
                
        # Rule 2: Keep only top 5 most recent runs
        if len(remaining_entries) > 5:
            remaining_entries.sort(key=lambda x: x[1], reverse=True)
            for path, mtime in remaining_entries[5:]:
                try:
                    shutil.rmtree(path)
                    self.logger.info(f"Garbage collector: Capped scaffolds size. Deleted older scaffold: {path}")
                    cleaned_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to delete directory {path}: {e}")
                    
        return {
            "status": "completed",
            "department": self.department,
            "cleaned_dirs": cleaned_count
        }
