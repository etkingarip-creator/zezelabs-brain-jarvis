"""
Zezelabs Holding OS - AppFactoryAgent
Gerçek LLM Entegrasyonlu Ajan
"""
import os
import re
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
            f"3. app/main.py: SADECE Python STANDART KÜTÜPHANE (http.server vb.) — harici paket (fastapi/flask) KULLANMA. "
            f"Saf, test edilebilir fonksiyonlar (örn. health()→dict) + /health endpoint'i + config'i os.getenv'den oku (secret gömme).\n"
            f"4. tests/test_smoke.py: HARİCİ BAĞIMLILIK OLMADAN (pytest+stdlib) GEÇECEK test. app.main'den saf fonksiyonları import edip doğrula.\n\n"
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
        # HEP-YA-HİÇ TUTARLILIK: herhangi bir dosya eksik/geçersiz/syntax-hatalıysa, LLM+fallback
        # KARIŞIMI uyumsuz app üretir (LLM main.py + fallback test → import uyuşmazlığı). O yüzden
        # tek bir dosya bile bozuksa TÜM seti tutarlı stdlib fallback'ten kur.
        use_fallback = False
        for rf in required_files:
            if rf not in files or not isinstance(files[rf], str) or not files[rf].strip():
                use_fallback = True
                break
            if not self._validate_code_syntax(rf, files[rf]):
                use_fallback = True
                break
        if use_fallback:
            self.logger.warning(f"[{task_id}] LLM çıktısı eksik/geçersiz → tutarlı stdlib fallback seti kullanılıyor.")
            files = {rf: self._get_fallback_template(rf, goal) for rf in required_files}

        tool_results = []
        for rel_path, content in files.items():
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
            
        # F1 — GERÇEK DOĞRULAMA: app'i çalıştır (syntax+import+pytest). Sahte-yeşil YASAK.
        verify = self._verify_scaffold(scaffold_dir)
        success = verify["verified"]
        self.logger.info(f"[{task_id}] Scaffold doğrulama: {verify['status']} (verified={success})")

        return AgentResult(
            task_id=task_id,
            department=DepartmentName.APP_FACTORY,
            success=success,
            output=(f"Scaffold for '{goal}' — DOĞRULAMA: {verify['status']}. "
                    f"{'✅ Çalışır (test geçti)' if success else '⚠️ ' + verify['detail']}"),
            tool_results=tool_results
        )

    def _verify_scaffold(self, scaffold_dir: str) -> Dict[str, Any]:
        """F1 — üretilen app GERÇEKTEN çalışıyor mu? syntax → import → pytest.
        verified=True SADECE pytest gerçek-yeşilse. Eksik bağımlılık 'çalışmadı' değil ayrı sınıf."""
        import subprocess
        import sys as _sys
        # 1. syntax: tüm .py
        for dp, _, files in os.walk(scaffold_dir):
            for fn in files:
                if fn.endswith(".py"):
                    try:
                        import py_compile
                        py_compile.compile(os.path.join(dp, fn), doraise=True)
                    except Exception as e:
                        return {"verified": False, "status": "SYNTAX_FAIL", "detail": f"{fn}: {e}"}
        # 2. pytest (gerçek çalıştırma)
        try:
            r = subprocess.run([_sys.executable, "-m", "pytest", "-q", scaffold_dir],
                               capture_output=True, text=True, timeout=120, cwd=scaffold_dir)
            raw = (r.stdout + "\n" + r.stderr)
        except Exception as e:
            return {"verified": False, "status": "TEST_ÇALIŞMADI", "detail": str(e)[:200]}
        low = raw.lower()
        # eksik bağımlılık → dürüstçe 'doğrulanamadı' (başarısızlık değil ayrı sınıf)
        if "modulenotfounderror" in low or "no module named" in low:
            mod = re.search(r"no module named ['\"]([\w\.]+)", low)
            return {"verified": False, "status": "BAĞIMLILIK_EKSİK",
                    "detail": f"Eksik paket: {mod.group(1) if mod else '?'} (pip install gerekli)"}
        passed = int((re.search(r"(\d+) passed", raw) or [0, 0])[1]) if re.search(r"(\d+) passed", raw) else 0
        failed = int((re.search(r"(\d+) failed", raw) or [0, 0])[1]) if re.search(r"(\d+) failed", raw) else 0
        errors = int((re.search(r"(\d+) error", raw) or [0, 0])[1]) if re.search(r"(\d+) error", raw) else 0
        if passed > 0 and failed == 0 and errors == 0:
            return {"verified": True, "status": "ÇALIŞIR", "detail": f"{passed} test geçti"}
        if "no tests ran" in low or (passed == 0 and failed == 0 and errors == 0):
            return {"verified": False, "status": "TEST_YOK", "detail": "geçen test yok (gerçek-yeşil değil)"}
        return {"verified": False, "status": "TEST_FAIL", "detail": f"passed={passed} failed={failed} errors={errors}"}

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
        """STDLIB-ONLY fallback: harici bağımlılık YOK → gerçekten çalışır ve test GEÇER (F1
        doğrulanabilir). FastAPI fallback'i doğrulanamıyordu (deps_missing). Bağımsız + sağlık
        endpoint'i + config/secret ayrımı (uzmanlık paketi prensibi)."""
        if filename == "README.md":
            return (
                f"# {goal}\n\nZezeLabs AppFactory tarafından üretildi (stdlib-only, bağımlılıksız).\n\n"
                f"## Çalıştırma\n```bash\npython -m app.main   # http://localhost:8000\n```\n"
                f"## Test\n```bash\npytest -q\n```\n## Sağlık\n`GET /health` → {{\"status\":\"ok\"}}\n")
        if filename == "manifest.json":
            return json.dumps({"name": "zezelabs-scaffold", "version": "1.0.0",
                               "description": f"{goal}", "runtime": "python-stdlib",
                               "dependencies": {}, "entrypoint": "app/main.py",
                               "endpoints": ["/", "/health"]}, indent=2, ensure_ascii=False)
        if filename == "app/main.py":
            return (
                "import os\nimport json\nfrom http.server import BaseHTTPRequestHandler, HTTPServer\n\n"
                "# config/secret ayrımı (uzmanlık prensibi): env'den oku, kod gömme\n"
                "CONFIG = {\"port\": int(os.getenv(\"PORT\", \"8000\")),\n"
                "          \"app_name\": os.getenv(\"APP_NAME\", " + repr(goal) + ")}\n\n"
                "def health() -> dict:\n    \"\"\"Sağlık kontrolü — saf, test edilebilir.\"\"\"\n"
                "    return {\"status\": \"ok\", \"app\": CONFIG[\"app_name\"]}\n\n"
                "def root() -> dict:\n    return {\"message\": \"ZezeLabs scaffold çalışıyor\", \"app\": CONFIG[\"app_name\"]}\n\n"
                "class Handler(BaseHTTPRequestHandler):\n"
                "    def do_GET(self):\n"
                "        payload = health() if self.path == \"/health\" else root()\n"
                "        body = json.dumps(payload).encode()\n"
                "        self.send_response(200)\n"
                "        self.send_header(\"Content-Type\", \"application/json\")\n"
                "        self.end_headers()\n        self.wfile.write(body)\n\n"
                "def run():\n    HTTPServer((\"\", CONFIG[\"port\"]), Handler).serve_forever()\n\n"
                "if __name__ == \"__main__\":\n    run()\n")
        if filename == "tests/test_smoke.py":
            return (
                "import os, sys\nsys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))\n"
                "from app.main import health, root\n\n"
                "def test_health():\n    assert health()[\"status\"] == \"ok\"\n\n"
                "def test_root():\n    assert \"message\" in root()\n")
        return ""

    def _get_fallback_template_legacy(self, filename: str, goal: str) -> str:
        """(Eski FastAPI şablonları — referans; varsayılan stdlib fallback kullanılıyor.)"""
        goal_lower = goal.lower()
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
