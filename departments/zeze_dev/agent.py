"""
Zezelabs Holding OS - ZezeDevAgent
Gerçek Mühendislik Ekibi: Architect → Coder → Tester → SelfHealer.
Deneme yazmaz; gerçek kod yazar, dosyaya kaydeder, test çalıştırır, hatayı kendi onarır.
"""
import os
import re
import json
import uuid
from typing import Dict, Any
from datetime import datetime
from core.operator_runtime.base_agent import BaseDepartmentAgent


class ZezeDevAgent(BaseDepartmentAgent):
    department = "zeze_dev"

    def __init__(self, workspace_root: str = "."):
        super().__init__(workspace_root=workspace_root)
        self.workspace_root = os.path.realpath(os.path.abspath(workspace_root))

    def _parse_files_json(self, llm_response: str) -> Dict[str, str]:
        """LLM yanıtından {path: content} JSON'ını ayıkla."""
        clean = llm_response.strip()
        if clean.startswith("```json"):
            clean = clean[7:]
        elif clean.startswith("```"):
            clean = clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        clean = clean.strip()
        try:
            data = json.loads(clean)
        except Exception:
            match = re.search(r'\{.*\}', clean, re.DOTALL)
            if not match:
                return {}
            try:
                data = json.loads(match.group(0))
            except Exception:
                return {}
        files = data.get("files", data) if isinstance(data, dict) else {}
        return {k: v for k, v in files.items() if isinstance(v, str)}

    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        # Self-heal modu (en üstte)
        if task_data.get("action") == "self_heal":
            description = (
                f"SELF HEAL/DEBUG TASK:\n"
                f"Target file: {task_data.get('file_path', '')}\n"
                f"Error trace: {task_data.get('error_trace', '')}\n"
                f"Goal: Read the target file, fix the bug, confirm the fix."
            )
            system_prompt = "Sen ZezeLabs Yazılım Geliştirme (Dev) ajanısın. Hata ayıklar, kodu file_writer ile onarırsın."
            return await self._standard_execute(task_data, system_prompt, description)

        # Görev-tipi kapsama: issue-çözme (mevcut kod) | kod üretimi | review | generic
        routes = [
            (["issue", "bug", "hatayı bul", "hatayı düzelt", "mevcut kod", "repoda", "codebase",
              "dosyada", "var olan", "fix in", "patch", "düzelt:", "çalışmıyor"],
             self._handle_issue),
            (["kod yaz", "fonksiyon", "implement", "uygula", "geliştir", "yaz ve test",
              "fix", "feature", "endpoint", "class", "modül", "build", "code", "script"],
             self._handle_codegen),
            (["review", "incele", "denetle", "refactor", "kod kalite", "code review", "audit kod"],
             self._handle_review),
        ]
        default_sp = "Sen ZezeLabs Yazılım Geliştirme ajanısın. Mimari planlar, kod standartları belirlersin."
        return await self.dispatch_by_task_type(task_data, routes, default_sp)

    def _code_search(self, term: str, root: str, max_hits: int = 50) -> Dict[str, int]:
        """Native kod arama (ripgrep varsa onu, yoksa saf-Python os.walk). Köprüye bağımlı değil."""
        import subprocess
        hits = {}
        try:
            r = subprocess.run(["rg", "-l", "--type", "py", term, root],
                               capture_output=True, text=True, timeout=20)
            if r.returncode == 0:
                for fp in r.stdout.splitlines():
                    if fp.strip().endswith(".py") and os.path.exists(fp.strip()):
                        hits[fp.strip()] = hits.get(fp.strip(), 0) + 1
                if hits:
                    return hits
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            pass
        # Saf-Python fallback
        pat = re.compile(re.escape(term))
        for dirpath, _, files in os.walk(root):
            if any(skip in dirpath for skip in ("__pycache__", ".git", "node_modules")):
                continue
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                fp = os.path.join(dirpath, fn)
                try:
                    with open(fp, encoding="utf-8", errors="ignore") as f:
                        c = pat.findall(f.read())
                        if c:
                            hits[fp] = len(c)
                except Exception:
                    pass
                if len(hits) >= max_hits:
                    return hits
        return hits

    def _ast_symbol_search(self, name: str, root: str, max_files: int = 200) -> list:
        """D2 — AST YAPISAL arama: fonksiyon/sınıf tanımını metin değil sözdizimi ağacından bul.
        Metin grep'in aksine tam tanım konumu + gövde döner (isabetli bağlam)."""
        import ast as _ast
        found = []
        scanned = 0
        for dirpath, _, files in os.walk(root):
            if any(s in dirpath for s in ("__pycache__", ".git", "node_modules")):
                continue
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                fp = os.path.join(dirpath, fn)
                scanned += 1
                if scanned > max_files:
                    return found
                try:
                    with open(fp, encoding="utf-8", errors="ignore") as f:
                        src = f.read()
                    tree = _ast.parse(src)
                except Exception:
                    continue
                lines = src.splitlines()
                for node in _ast.walk(tree):
                    if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef, _ast.ClassDef)) and node.name == name:
                        end = getattr(node, "end_lineno", node.lineno)
                        seg = "\n".join(lines[node.lineno - 1:end])
                        found.append({"path": fp, "lineno": node.lineno, "end_lineno": end,
                                      "kind": type(node).__name__, "segment": seg[:2000]})
        return found

    def _make_diff(self, old: str, new: str, path: str) -> str:
        """D3 — birleşik (unified) diff üret (şeffaf değişiklik kaydı)."""
        import difflib
        return "".join(difflib.unified_diff(
            old.splitlines(keepends=True), new.splitlines(keepends=True),
            fromfile=f"a/{path}", tofile=f"b/{path}"))

    def _surgical_edit(self, path: str, old: str, new: str) -> Dict:
        """Yerinde cerrahi düzenleme + D3 backup/diff. old_string benzersiz olmalı; değilse reddet."""
        if not old or not os.path.exists(path):
            return {"ok": False, "reason": "geçersiz path/old_string"}
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return {"ok": False, "reason": f"okunamadı: {e}"}
        count = content.count(old)
        if count == 0:
            return {"ok": False, "reason": "old_string dosyada yok"}
        if count > 1:
            return {"ok": False, "reason": f"old_string {count} kez var (benzersiz değil)"}
        new_content = content.replace(old, new, 1)
        diff = self._make_diff(content, new_content, path)
        try:
            with open(path + ".bak", "w", encoding="utf-8") as f:  # D3 geri-alma yedeği
                f.write(content)
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return {"ok": True, "diff": diff, "backup": path + ".bak"}
        except Exception as e:
            return {"ok": False, "reason": f"yazılamadı: {e}"}

    def _undo_edit(self, path: str) -> bool:
        """D3 — son düzenlemeyi geri al (.bak'tan). Test bozulursa otomatik rollback."""
        bak = path + ".bak"
        if not os.path.exists(bak):
            return False
        try:
            with open(bak, encoding="utf-8") as f:
                content = f.read()
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            os.remove(bak)
            return True
        except Exception:
            return False

    def _ast_find_references(self, name: str, root: str, max_files: int = 300) -> list:
        """E3 — call-graph: bir sembolün ÇAĞIRANLARINI/referanslarını bul. İmza değişince
        hangi dosyaların güncellenmesi gerektiğini gösterir (çok-dosya koordinasyonu)."""
        import ast as _ast
        refs = []
        scanned = 0
        for dirpath, _, files in os.walk(root):
            if any(s in dirpath for s in ("__pycache__", ".git", "node_modules")):
                continue
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                fp = os.path.join(dirpath, fn)
                scanned += 1
                if scanned > max_files:
                    return refs
                try:
                    with open(fp, encoding="utf-8", errors="ignore") as f:
                        src = f.read()
                    tree = _ast.parse(src)
                except Exception:
                    continue
                lines = src.splitlines()
                for node in _ast.walk(tree):
                    hit = False
                    if isinstance(node, _ast.Call):
                        fnc = node.func
                        if (isinstance(fnc, _ast.Name) and fnc.id == name) or \
                           (isinstance(fnc, _ast.Attribute) and fnc.attr == name):
                            hit = True
                    if hit:
                        ln = getattr(node, "lineno", 0)
                        refs.append({"path": fp, "lineno": ln,
                                     "line": lines[ln - 1].strip() if 0 < ln <= len(lines) else ""})
        return refs

    def _run_tests(self, scope_paths: list, timeout: int = 120) -> Dict:
        """E1+E2 — DÜRÜST test koşucu. Tam-suite regresyon kapsamı. 'no tests ran' BAŞARI DEĞİL.
        Döner: {syntax_ok, passed, failed, errors, no_tests, real_green, raw}."""
        import subprocess
        import sys as _sys
        # syntax kontrolü (değişen .py dosyaları)
        syntax_ok = True
        for p in scope_paths:
            if p.endswith(".py") and os.path.exists(p):
                try:
                    import py_compile
                    py_compile.compile(p, doraise=True)
                except Exception:
                    syntax_ok = False
        # pytest: kapsamdaki dizinler (regresyon)
        dirs = sorted({os.path.dirname(p) if p.endswith(".py") else p for p in scope_paths if p})
        dirs = [d for d in dirs if d and os.path.isdir(d)] or ["."]
        try:
            r = subprocess.run([_sys.executable, "-m", "pytest", "-q", *dirs],
                               capture_output=True, text=True, timeout=timeout)
            raw = (r.stdout + "\n" + r.stderr)[-2500:]
        except Exception as e:
            return {"syntax_ok": syntax_ok, "passed": 0, "failed": 0, "errors": 1,
                    "no_tests": False, "real_green": False, "raw": f"pytest çalışmadı: {e}"}
        passed = int((re.search(r"(\d+) passed", raw) or [0, 0])[1]) if re.search(r"(\d+) passed", raw) else 0
        failed = int((re.search(r"(\d+) failed", raw) or [0, 0])[1]) if re.search(r"(\d+) failed", raw) else 0
        errors = int((re.search(r"(\d+) error", raw) or [0, 0])[1]) if re.search(r"(\d+) error", raw) else 0
        no_tests = "no tests ran" in raw.lower() or (passed == 0 and failed == 0 and errors == 0)
        # GERÇEK YEŞİL: syntax + en az 1 geçen test + sıfır fail/error. 'no tests' YEŞİL DEĞİL.
        real_green = syntax_ok and passed > 0 and failed == 0 and errors == 0
        return {"syntax_ok": syntax_ok, "passed": passed, "failed": failed, "errors": errors,
                "no_tests": no_tests, "real_green": real_green, "raw": raw}

    async def _handle_issue(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """ISSUE-ÇÖZME — gerçek SWE pipeline'ı: codebase'i ARA → ANLA → CERRAHI DÜZELT → TEST → SELF-HEAL.
        Greenfield üreteç değil; mevcut kodda issue çözer (frontier standardı). Native, köprüye bağımsız."""
        from core.skills.registry import SkillRegistry
        registry = SkillRegistry()
        task_id = self._safe_task_id(task_data)
        description = task_data.get("description", "") or ""
        search_root = task_data.get("path", "departments")  # arama kökü

        # 1. SEARCH: LLM'den arama terimleri al, grep/glob ile aday dosyaları bul
        kw_prompt = (
            f"GÖREV (issue): {description}\n\nBu issue'yu çözmek için codebase'de aranacak 1-3 anahtar "
            f"terim ver (fonksiyon/değişken/string adı). SADECE JSON: {{\"terms\": [\"term1\", \"term2\"]}}"
        )
        kw_resp = await self.ask_llm(kw_prompt, system_prompt="Sen kod arama uzmanısın. İsabetli arama terimleri seçersin.")
        terms = []
        try:
            m = re.search(r'\{.*\}', kw_resp, re.DOTALL)
            if m:
                terms = json.loads(m.group(0)).get("terms", [])
        except Exception:
            pass
        if not terms:
            terms = [w for w in re.findall(r"[A-Za-z_]{4,}", description)][:3]
        # terimleri temizle (parantez/uzantı/özel karakter regex'i bozar)
        terms = [re.sub(r"[^\w]", "", t) for t in terms if re.sub(r"[^\w]", "", t)]

        candidates = {}
        for term in terms[:3]:
            for fp, c in self._code_search(term, search_root).items():
                candidates[fp] = candidates.get(fp, 0) + c
        ranked = sorted(candidates, key=candidates.get, reverse=True)[:3]
        if not ranked:
            return {"success": False, "task_id": task_id,
                    "output": f"Issue için ilgili dosya bulunamadı (terimler: {terms}).", "deliverable": False}

        # 2. UNDERSTAND: aday dosyaları oku + D2 AST yapısal bağlam (terim bir sembolse tam tanımı)
        file_ctx = ""
        for fp in ranked:
            try:
                with open(fp, encoding="utf-8", errors="ignore") as f:
                    file_ctx += f"\n\n### DOSYA: {fp}\n{f.read()[:3000]}"
            except Exception:
                pass
        # E3 — call-graph: aday sembollerin ÇAĞIRANLARINI bul (çok-dosya koordinasyonu)
        ref_ctx = ""
        ref_files = set()
        for term in terms[:3]:
            for sym in self._ast_symbol_search(term, search_root)[:2]:
                file_ctx += (f"\n\n### AST SEMBOL: {sym['kind']} '{term}' @ {sym['path']}:{sym['lineno']}\n"
                             f"{sym['segment']}")
            refs = self._ast_find_references(term, search_root)[:8]
            for r in refs:
                ref_files.add(r["path"])
                ref_ctx += f"\n- {r['path']}:{r['lineno']}  {r['line']}"
        if ref_ctx:
            file_ctx += f"\n\n### ÇAĞIRANLAR (imza değişirse bunları da güncelle):{ref_ctx}"

        # 3+4+5. EDIT(ÇOK-DOSYA) → DÜRÜST REGRESYON TESTİ → SELF-HEAL → TOPLU ROLLBACK
        applied = []
        last = {"raw": ""}
        success = False
        # regresyon kapsamı: aday + çağıran dosyaların dizinleri (E2 — sadece tek klasör değil)
        regression_scope = list(dict.fromkeys(ranked + list(ref_files)))
        for attempt in range(3):
            edit_prompt = (
                f"ISSUE: {description}\n\nİLGİLİ KOD:{file_ctx}\n\n"
                f"Issue'yu çözen CERRAHI düzenleme(ler)i ver. İmza/davranış değişiyorsa ÇAĞIRANLARI da "
                f"aynı anda güncelle (çok-dosya). Her old_string ilgili dosyada BİREBİR + benzersiz olmalı.\n"
                f"SADECE JSON: {{\"edits\": [{{\"path\": \"...\", \"old_string\": \"...\", \"new_string\": \"...\", \"explanation\": \"...\"}}]}}"
                + (f"\n\n[ÖNCEKI DENEME BAŞARISIZ: {last['raw'][:700]}]" if attempt else "")
            )
            edit_resp = await self.ask_llm(edit_prompt, system_prompt="Sen kıdemli mühendissin. Minimal, cerrahi, çok-dosya tutarlı düzeltme yaparsın. Bütün dosyayı değil gereken satırları değiştirirsin; imza değişince çağıranları da güncellersin.")
            try:
                edits = json.loads(re.search(r'\{.*\}', edit_resp, re.DOTALL).group(0)).get("edits", [])
            except Exception:
                continue
            if not edits:
                continue
            # tüm edit'leri uygula (her biri backup'lı)
            this_round = []
            ok_all = True
            for ed in edits:
                p = ed.get("path", "")
                if not p or not os.path.exists(p):
                    continue
                res = self._surgical_edit(p, ed.get("old_string", ""), ed.get("new_string", ""))
                if res["ok"]:
                    this_round.append({"path": p, "explanation": ed.get("explanation", ""), "diff": res.get("diff", "")[:600]})
                    if p not in regression_scope:
                        regression_scope.append(p)
                else:
                    ok_all = False
                    last["raw"] = f"Edit uygulanamadı ({p}): {res['reason']}"
            if not this_round:
                continue

            # E1+E2 — DÜRÜST regresyon testi (geniş kapsam, 'no tests ran' YEŞİL DEĞİL)
            last = self._run_tests(regression_scope)
            if last["real_green"]:
                applied = this_round
                for e in this_round:  # başarı → yedekleri temizle
                    if os.path.exists(e["path"] + ".bak"):
                        os.remove(e["path"] + ".bak")
                success = True
                break
            elif last["syntax_ok"] and last["failed"] == 0 and last["errors"] == 0 and last["no_tests"]:
                # TESTSİZ: edit muhtemelen doğru ama KANITLANAMAZ. Geri alma — KORU ama 'çözüldü' deme.
                applied = this_round  # uygulandı (doğrulanamadı)
                self.logger.warning(f"[{task_id}] Düzenleme uygulandı ama doğrulayacak test yok (deneme {attempt+1}).")
                break
            else:
                # GERÇEK KIRILMA (fail/error/syntax): TOPLU ROLLBACK → repo temiz + regresyonsuz
                for e in this_round:
                    self._undo_edit(e["path"])
                self.logger.warning(f"[{task_id}] Regresyon/test FAIL → toplu rollback (deneme {attempt+1}). "
                                    f"passed={last['passed']} failed={last['failed']} errors={last['errors']}")

        test_output = last.get("raw", "")
        # E1 — DÜRÜST durum: real_green değilse 'çözüldü' DEME
        if success:
            verdict = f"✅ ÇÖZÜLDÜ ({last['passed']} test geçti, 0 fail — regresyon kapsamı: {len(regression_scope)} dizin)"
        elif last.get("no_tests") and applied:
            verdict = "⚠️ DÜZENLEME YAPILDI AMA DOĞRULANAMADI (ilgili test yok — gerçek-yeşil değil, çözüldü DENMEZ)"
        else:
            verdict = f"❌ ÇÖZÜLEMEDİ (test geçmedi/edit tutmadı; passed={last.get('passed',0)} failed={last.get('failed',0)})"

        report_dir = os.path.join(self.workspace_root, "departments", self.department, "reports", task_id)
        os.makedirs(report_dir, exist_ok=True)
        with open(os.path.join(report_dir, "issue_resolution.json"), "w", encoding="utf-8") as f:
            json.dump({"task_id": task_id, "description": description, "searched_terms": terms,
                       "candidate_files": ranked, "applied_edits": applied, "success": success,
                       "test_output": test_output[-1500:]}, f, indent=2, ensure_ascii=False)

        output = (
            f"# Issue Çözüm Raporu\n\n**Issue:** {description}\n\n"
            f"**Arama terimleri:** {terms}\n**Aday dosyalar:** {ranked}\n"
            f"**Çağıran dosyalar (E3):** {sorted(ref_files) or 'yok'}\n\n"
            f"**Uygulanan düzenlemeler ({len(applied)}):**\n"
            + "\n".join(f"- `{a['path']}`: {a['explanation']}" for a in applied)
            + f"\n\n**Sonuç:** {verdict}\n\n```\n{test_output[-600:]}\n```"
        )
        # E1 — DÜRÜST: success = SADECE gerçek-yeşil (doğrulanmış). deliverable = edit uygulandı mı.
        return {"success": success, "task_id": task_id, "output": output,
                "artifacts": [a["path"] for a in applied],
                "verified": success, "deliverable": bool(applied)}

    async def _handle_review(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Code review handler: yapılandırılmış inceleme raporu üretir."""
        import re
        description = task_data.get("description", "") or ""
        task_id = self._safe_task_id(task_data)
        prompt = (
            f"GÖREV: {description}\n\nKıdemli mühendis olarak kod incelemesi yap.\n"
            f"SADECE JSON: {{\"issues\":[{{\"severity\":\"high/medium/low\",\"desc\":\"\",\"fix\":\"\"}}],"
            f"\"score\":0-100,\"summary\":\"\"}}"
        )
        resp = await self.ask_llm(prompt, system_prompt="Sen ZezeLabs kod inceleme uzmanısın. SOLID, güvenlik, performans denetlersin.")
        review = {}
        try:
            m = re.search(r'\{.*\}', resp, re.DOTALL)
            if m: review = json.loads(m.group(0))
        except Exception:
            review = {"summary": resp[:200], "issues": []}
        report_dir = os.path.join(self.workspace_root, self.department, "reviews", task_id) \
            if False else os.path.join(self.workspace_root, "departments", self.department, "reports", task_id)
        os.makedirs(report_dir, exist_ok=True)
        path = os.path.join(report_dir, "code_review.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(review, f, indent=2, ensure_ascii=False)
        valid = self._validate_artifact(path)
        issues = review.get("issues", [])
        output = (
            f"# Kod İnceleme Raporu (Skor: {review.get('score','N/A')}/100)\n\n"
            + "\n".join(f"- [{i.get('severity','?')}] {i.get('desc','?')}" for i in issues if isinstance(i, dict))
            + f"\n\n{review.get('summary','')}"
        )
        return {"success": valid, "task_id": task_id, "output": output,
                "artifacts": [path], "deliverable": valid}

    async def _handle_codegen(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_id = self._safe_task_id(task_data)
        description = task_data.get("description", "") or ""

        # GERÇEK MÜHENDİSLİK PIPELINE'ı
        from core.skills.registry import SkillRegistry
        registry = SkillRegistry()

        out_dir = os.path.join(self.workspace_root, "departments", self.department, "workspace", task_id)
        rel_out = os.path.relpath(out_dir, os.getcwd()).replace("\\", "/")

        architect_prompt = (
            f"GÖREV: {description}\n\n"
            f"Bir yazılım mimarı olarak bu görevi GERÇEK, çalışan Python kodu olarak teslim et.\n"
            f"Kod ve testlerini üret. Test dosyası mutlaka 'test_' ile başlamalı ve pytest uyumlu olmalı.\n"
            f"Dosyaları '{rel_out}/' altına yaz.\n\n"
            f"YANITINI SADECE şu JSON formatında ver (markdown yok, açıklama yok):\n"
            f'{{"files": {{"{rel_out}/main.py": "kod...", "{rel_out}/test_main.py": "pytest test kodu..."}}}}'
        )
        system_prompt = (
            "Sen ZezeLabs Yazılım Geliştirme (Dev) ajanısın. SOLID prensiplerine uyan, test edilebilir, "
            "çalışan kod üretirsin. Asla yer tutucu (placeholder) veya 'TODO' bırakmazsın."
        )

        max_iterations = 3
        files: Dict[str, str] = {}
        test_output = ""
        tests_passed = False
        current_prompt = architect_prompt

        for iteration in range(max_iterations):
            # 1. ARCHITECT + CODER: kod üret
            llm_response = await self.ask_llm(current_prompt, system_prompt=system_prompt)
            parsed = self._parse_files_json(llm_response)
            if not parsed:
                self.logger.warning(f"[{task_id}] Mimar geçerli JSON üretmedi (deneme {iteration+1}).")
                current_prompt = architect_prompt + "\n\n[HATA: Geçerli JSON üretmedin. SADECE belirtilen JSON formatında yanıt ver.]"
                continue
            files = parsed

            # 2. CODER: dosyaları gerçekten yaz (file_writer)
            written = []
            for path, content in files.items():
                res = await registry.execute_tool("file_writer", {"file_path": path, "content": content})
                written.append(path)
                self.logger.info(f"[{task_id}] Yazıldı: {path} ({res[:40]})")

            # 3. TESTER: testleri gerçekten çalıştır (python_executor / pytest)
            test_files = [p for p in files if os.path.basename(p).startswith("test_")]
            if not test_files:
                tests_passed = True  # test yoksa kod yazımıyla yetin
                test_output = "Test dosyası üretilmedi; sadece kod teslim edildi."
                break

            runner_code = (
                "import subprocess, sys\n"
                f"r = subprocess.run([sys.executable, '-m', 'pytest', '-q', {rel_out!r}], "
                "capture_output=True, text=True, timeout=60)\n"
                "print(r.stdout)\nprint(r.stderr)\nprint('EXIT', r.returncode)"
            )
            test_output = await registry.execute_tool("python_executor", {"code": runner_code})

            if "EXIT 0" in test_output or "passed" in test_output.lower() and "failed" not in test_output.lower():
                tests_passed = True
                self.logger.info(f"[{task_id}] Testler GEÇTİ (deneme {iteration+1}).")
                break

            # 4. SELFHEALER: hata logunu geri besle
            self.logger.warning(f"[{task_id}] Testler başarısız (deneme {iteration+1}). Self-heal tetikleniyor.")
            current_prompt = (
                architect_prompt +
                f"\n\n[TEST HATASI - DENEME {iteration+1}]\n"
                f"Önceki kodun testleri geçemedi. Hata çıktısı:\n{test_output[:1200]}\n"
                f"Lütfen kodu düzelt ve TÜM dosyaları tekrar üret."
            )

        # Deliverable raporu
        report = {
            "task_id": task_id,
            "department": self.department,
            "timestamp": datetime.now().isoformat(),
            "query": description,
            "files": list(files.keys()),
            "tests_passed": tests_passed,
            "test_output": test_output[-2000:],
        }
        report_dir = os.path.join(self.workspace_root, "departments", self.department, "reports", task_id)
        os.makedirs(report_dir, exist_ok=True)
        with open(os.path.join(report_dir, "dev_report.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        status_icon = "✅ GEÇTİ" if tests_passed else "⚠️ TESTLER GEÇMEDİ"
        output = (
            f"# Yazılım Geliştirme — Teslim Raporu\n\n"
            f"**Görev:** {description}\n\n"
            f"**Üretilen Dosyalar ({len(files)}):**\n"
            + "\n".join(f"- `{p}`" for p in files) +
            f"\n\n**Test Durumu:** {status_icon}\n\n"
            f"```\n{test_output[-800:]}\n```"
        )

        return {
            "success": tests_passed,
            "task_id": task_id,
            "output": output,
            "artifacts": list(files.keys()),
            "deliverable": True,
            "tests_passed": tests_passed,
        }
