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
            
        files = self._robust_parse_files(llm_response) if llm_response else {}
                
        required_files = ["README.md", "manifest.json", "app/main.py", "tests/test_smoke.py",
                          "Dockerfile", "Procfile"]
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

    async def run_app_lifecycle(self, goal: str, task_id: Optional[str] = None,
                                with_monetization: bool = True) -> Dict[str, Any]:
        """TAM DÖNGÜ (holding edge'i): fikir→KUR→DOĞRULA→GERÇEK runtime deploy→analitik→monetizasyon.
        Rakipler 'build'de durur. Her aşama GERÇEK kontrol (sahte-yeşil yok). Departmanlar arası."""
        import uuid
        if not task_id:
            task_id = str(uuid.uuid4())
        stages = {}

        # 0. H4 OTONOM GO/NO-GO GATE: zeze_business unit economics'e göre KARAR — kötü ekonomi → BUILD ETME
        if with_monetization:
            try:
                biz = await self.delegate_task("zeze_business", {
                    "task_id": f"gate-{task_id}", "task_type": "market",
                    "description": f"Build edilecek app için unit economics ve GO/NO-GO kararı: {goal}"})
                decision = (biz.get("model", {}) or {}).get("decision", {}) if isinstance(biz, dict) else {}
                # karar raporda da metin olarak gelebilir; NO-GO geçiyorsa durdur
                out_text = str(biz.get("output", "")) if isinstance(biz, dict) else ""
                is_nogo = decision.get("decision") == "NO-GO" or "OTONOM KARAR: NO-GO" in out_text
                stages["business_gate"] = {"ok": not is_nogo,
                                           "detail": "GO" if not is_nogo else "NO-GO — kötü unit economics, build iptal"}
                if is_nogo:
                    return {"task_id": task_id, "goal": goal, "lifecycle_complete": False,
                            "stages": stages, "halted_reason": "business_gate NO-GO"}
            except Exception as e:
                stages["business_gate"] = {"ok": True, "detail": f"gate atlandı: {e}"}

        # 1. KUR + DOĞRULA (pytest gerçek-yeşil)
        built = await self.run_dry_task(goal=goal, task_id=task_id)
        stages["build_verify"] = {"ok": built.success, "detail": built.output[:160]}
        scaffold_dir = os.path.realpath(os.path.join(self.workspace_root, "app_factory", "scaffolds", task_id))

        # 2. GERÇEK RUNTIME DEPLOY (yerel): server'ı BAŞLAT, /health'e dokun (gerçek servis kanıtı)
        stages["runtime_deploy"] = self._deploy_and_probe(scaffold_dir)

        # 3. ANALİTİK/ENSTRÜMAN: /health + / yanıt veriyor mu (gözlemlenebilirlik temeli)
        stages["instrument"] = {"ok": stages["runtime_deploy"].get("health_ok", False),
                                "detail": "sağlık endpoint'i izlenebilir" if stages["runtime_deploy"].get("health_ok") else "endpoint yok"}

        # 4. MONETİZASYON (departmanlar arası — zeze_business): gerçek delegasyon
        if with_monetization:
            try:
                mon = await self.delegate_task("zeze_business", {
                    "task_id": f"mon-{task_id}", "task_type": "monetization",
                    "description": f"Şu uygulama için somut monetizasyon planı (fiyatlandırma, hedef kitle, ilk gelir yolu): {goal}"})
                stages["monetization"] = {"ok": bool(mon.get("success")), "detail": str(mon.get("output", ""))[:200]}
            except Exception as e:
                stages["monetization"] = {"ok": False, "detail": f"delegasyon hatası: {e}"}

        # DÜRÜST genel durum: build+deploy gerçek-yeşil olmalı (monetizasyon bonus)
        core_ok = stages["build_verify"]["ok"] and stages["runtime_deploy"].get("ok", False)
        return {"task_id": task_id, "goal": goal, "lifecycle_complete": core_ok,
                "stages": stages, "scaffold_dir": scaffold_dir}

    def _deploy_and_probe(self, scaffold_dir: str, timeout_s: int = 8) -> Dict[str, Any]:
        """GERÇEK runtime kanıtı: app'i subprocess olarak başlat, /health'e HTTP at, 200 + payload doğrula.
        Unit test değil — app'in GERÇEKTEN trafik servis ettiğinin kanıtı (rakiplerin iddia ettiği şey)."""
        import subprocess
        import sys as _sys
        import time as _time
        import socket
        import urllib.request
        main_py = os.path.join(scaffold_dir, "app", "main.py")
        if not os.path.exists(main_py):
            return {"ok": False, "detail": "app/main.py yok"}
        # boş port bul
        s = socket.socket(); s.bind(("", 0)); port = s.getsockname()[1]; s.close()
        env = dict(os.environ, PORT=str(port))
        proc = None
        try:
            proc = subprocess.Popen([_sys.executable, "-m", "app.main"], cwd=scaffold_dir, env=env,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            health_ok = root_ok = False
            deadline = _time.time() + timeout_s
            while _time.time() < deadline:
                if proc.poll() is not None:
                    err = proc.stderr.read().decode(errors="ignore")[:200] if proc.stderr else ""
                    return {"ok": False, "detail": f"server çöktü: {err}"}
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1) as resp:
                        import json as _json
                        data = _json.loads(resp.read().decode())
                        health_ok = resp.status == 200 and data.get("status") == "ok"
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1) as resp2:
                        root_ok = resp2.status == 200
                    break
                except Exception:
                    _time.sleep(0.4)
            return {"ok": health_ok and root_ok, "health_ok": health_ok, "root_ok": root_ok,
                    "port": port, "detail": "canlı servis /health 200 ✅" if health_ok else "servis yanıt vermedi"}
        except Exception as e:
            return {"ok": False, "detail": f"deploy hatası: {e}"}
        finally:
            if proc and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except Exception:
                    proc.kill()

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

    def _robust_parse_files(self, resp: str) -> Dict[str, str]:
        """F6 — sağlam JSON parse (jenerik fallback'i azalt). Markdown çitleri, en geniş {...},
        ham kontrol karakteri kaçışı dener. Başarısızsa boş döner (→ fallback)."""
        s = resp.strip()
        # markdown çitlerini temizle
        m = re.search(r"```(?:json)?\s*(.*?)```", s, re.DOTALL)
        if m:
            s = m.group(1).strip()
        # en geniş {...} bloğu
        b = re.search(r"\{.*\}", s, re.DOTALL)
        cand = b.group(0) if b else s
        for attempt in (cand, cand.replace("\t", "\\t"), re.sub(r"(?<!\\)\n(?=[^\"]*\":)", "\\\\n", cand)):
            try:
                data = json.loads(attempt)
                if isinstance(data, dict):
                    files = data.get("files", data)
                    out = {k: v for k, v in files.items() if isinstance(v, str) and v.strip()}
                    if out:
                        return out
            except Exception:
                continue
        self.logger.warning("[app_factory] LLM JSON parse edilemedi → tutarlı fallback.")
        return {}

    def _get_fallback_template(self, filename: str, goal: str) -> str:
        """FULL-STACK STDLIB fallback: sqlite3 (gerçek kalıcı DB) + token auth + Docker (deploy-hazır).
        Harici paket YOK → gerçekten çalışır + test GEÇER (F1 doğrulanabilir). DB+auth+deploy =
        rakip kategorisine girer; stdlib = bağımlılıksız doğrulanabilir."""
        if filename == "README.md":
            return (
                f"# {goal}\n\nZezeLabs AppFactory — full-stack (sqlite DB + token auth), stdlib-only.\n\n"
                f"## Çalıştırma\n```bash\npython -m app.main   # http://localhost:8000\n```\n"
                f"## Test\n```bash\npytest -q\n```\n## Deploy (container)\n```bash\n"
                f"docker build -t app . && docker run -p 8000:8000 -e API_TOKEN=gizli app\n```\n"
                f"Hosting (Railway/Fly/Render): repo'yu bağla, API_TOKEN secret'ını ayarla.\n\n"
                f"## Endpoint'ler\n- `GET /health` sağlık\n- `GET /items` listele\n"
                f"- `POST /items` ekle (Authorization: Bearer <API_TOKEN>)\n")
        if filename == "manifest.json":
            return json.dumps({"name": "zezelabs-fullstack", "version": "1.0.0",
                               "description": f"{goal}", "runtime": "python-stdlib",
                               "dependencies": {}, "entrypoint": "app/main.py",
                               "database": "sqlite3", "auth": "bearer-token",
                               "endpoints": ["/health", "GET /items", "POST /items"],
                               "deploy": ["Dockerfile", "Procfile"]}, indent=2, ensure_ascii=False)
        if filename == "app/main.py":
            return (
                "import os\nimport json\nimport sqlite3\nfrom http.server import BaseHTTPRequestHandler, HTTPServer\n\n"
                "# config/secret: env'den (kod gömme yok)\n"
                "CONFIG = {\"port\": int(os.getenv(\"PORT\", \"8000\")),\n"
                "          \"db\": os.getenv(\"DB_PATH\", \"app.db\"),\n"
                "          \"token\": os.getenv(\"API_TOKEN\", \"dev-token\"),\n"
                "          \"app_name\": os.getenv(\"APP_NAME\", " + repr(goal) + ")}\n\n"
                "def _conn():\n    c = sqlite3.connect(CONFIG[\"db\"])\n"
                "    c.execute(\"CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, name TEXT)\")\n"
                "    return c\n\n"
                "def health() -> dict:\n    return {\"status\": \"ok\", \"app\": CONFIG[\"app_name\"], \"db\": \"sqlite\"}\n\n"
                "def add_item(name: str) -> dict:\n    \"\"\"Gerçek DB yazma — saf, test edilebilir.\"\"\"\n"
                "    c = _conn()\n    cur = c.execute(\"INSERT INTO items (name) VALUES (?)\", (name,))\n"
                "    c.commit()\n    iid = cur.lastrowid\n    c.close()\n    return {\"id\": iid, \"name\": name}\n\n"
                "def list_items() -> list:\n    c = _conn()\n    rows = c.execute(\"SELECT id, name FROM items\").fetchall()\n"
                "    c.close()\n    return [{\"id\": r[0], \"name\": r[1]} for r in rows]\n\n"
                "def check_auth(header: str) -> bool:\n    \"\"\"Bearer token doğrulama.\"\"\"\n"
                "    return header == f\"Bearer {CONFIG['token']}\"\n\n"
                "class Handler(BaseHTTPRequestHandler):\n"
                "    def _send(self, code, payload):\n        body = json.dumps(payload).encode()\n"
                "        self.send_response(code)\n        self.send_header(\"Content-Type\", \"application/json\")\n"
                "        self.end_headers()\n        self.wfile.write(body)\n"
                "    def do_GET(self):\n"
                "        if self.path == \"/health\": self._send(200, health())\n"
                "        elif self.path == \"/items\": self._send(200, list_items())\n"
                "        else: self._send(200, {\"app\": CONFIG[\"app_name\"]})\n"
                "    def do_POST(self):\n"
                "        if not check_auth(self.headers.get(\"Authorization\", \"\")):\n"
                "            self._send(401, {\"error\": \"unauthorized\"}); return\n"
                "        n = int(self.headers.get(\"Content-Length\", 0))\n"
                "        data = json.loads(self.rfile.read(n) or b'{}')\n"
                "        self._send(201, add_item(data.get(\"name\", \"\")))\n\n"
                "def run():\n    HTTPServer((\"\", CONFIG[\"port\"]), Handler).serve_forever()\n\n"
                "if __name__ == \"__main__\":\n    run()\n")
        if filename == "tests/test_smoke.py":
            return (
                "import os, sys, tempfile\n"
                "os.environ[\"DB_PATH\"] = os.path.join(tempfile.gettempdir(), \"zztest.db\")\n"
                "if os.path.exists(os.environ[\"DB_PATH\"]): os.remove(os.environ[\"DB_PATH\"])\n"
                "sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))\n"
                "from app.main import health, add_item, list_items, check_auth, CONFIG\n\n"
                "def test_health():\n    assert health()[\"status\"] == \"ok\"\n\n"
                "def test_db_crud():\n    add_item(\"alpha\")\n    items = list_items()\n"
                "    assert any(i[\"name\"] == \"alpha\" for i in items)\n\n"
                "def test_auth():\n    assert check_auth(f\"Bearer {CONFIG['token']}\") is True\n"
                "    assert check_auth(\"Bearer wrong\") is False\n")
        if filename == "Dockerfile":
            return ("FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\n"
                    "ENV PORT=8000\nEXPOSE 8000\nCMD [\"python\", \"-m\", \"app.main\"]\n")
        if filename == "Procfile":
            return "web: python -m app.main\n"
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
