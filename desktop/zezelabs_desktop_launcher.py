# -*- coding: utf-8 -*-
"""
Zezelabs ZOM â€” tek giriÅŸ noktasÄ± (masaÃ¼stÃ¼ simgesi).
Backend (5000) + statik UI (5173) + uygulama penceresi.
"""
from __future__ import annotations

import os
import sys
import time
import logging
import socket
import urllib.request
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIST = ROOT / "frontend" / "dist"
FRONTEND_DIR = ROOT / "frontend"
LOG_DIR = ROOT / "logs"
LOG_FILE = LOG_DIR / "desktop_launcher.log"
# Lock dosyasÄ± kaldÄ±rÄ±ldÄ± - sadece port kontrolÃ¼ kullanÄ±lÄ±yor
LOCK_FILE = ROOT / "workspace" / ".zezelabs_desktop.lock"

BACKEND_HOST = os.getenv("ZOM_DESKTOP_BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = int(os.getenv("ZOM_DESKTOP_BACKEND_PORT", "5000"))
UI_PORT = int(os.getenv("ZOM_DESKTOP_UI_PORT", "5173"))

# Arka plan servisleri iÃ§in (konsol yok)
CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0
# GUI uygulamalarÄ± (Electron/tarayÄ±cÄ±) iÃ§in ASLA CREATE_NO_WINDOW kullanma
CREATE_NEW_GROUP = 0x00000200 if sys.platform == "win32" else 0
DETACHED_PROCESS = 0x00000008 if sys.platform == "win32" else 0


def _setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )
    return logging.getLogger("zezelabs.desktop")


log = _setup_logging()


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        try:
            import ctypes

            kernel = ctypes.windll.kernel32
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = kernel.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not handle:
                return False
            exit_code = ctypes.c_ulong()
            STILL_ACTIVE = 259
            if kernel.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                kernel.CloseHandle(handle)
                return exit_code.value == STILL_ACTIVE
            kernel.CloseHandle(handle)
        except Exception:
            pass
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex((BACKEND_HOST, port)) == 0


def _wait_url(url: str, timeout: int = 90) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(1)
    return False


def _desktop_env() -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env.setdefault("ZOM_ENABLE_AUTO_GITHUB_PUSH", "false")
    env.setdefault("ZOM_ENABLE_VOICE_LISTENER", "false")
    env.setdefault("ZOM_ENABLE_LEGACY_OPENCLAW_CLEANUP", "false")
    env.setdefault("ZOM_ENABLE_HERMES_GATEWAY", "false")
    env.setdefault("ZOM_ENABLE_OLLAMA_FALLBACK", "false")
    env.setdefault("ZOM_ENABLE_RABBITMQ", "false")
    return env


def _inject_runtime_config() -> None:
    index = FRONTEND_DIST / "index.html"
    if not index.exists():
        return
    api = f"http://{BACKEND_HOST}:{BACKEND_PORT}"
    ws = f"ws://{BACKEND_HOST}:{BACKEND_PORT}/ws"
    snippet = f'<script>window.__ZEZE_CONFIG__={{apiBase:"{api}",wsUrl:"{ws}"}};</script>'
    html = index.read_text(encoding="utf-8")
    
    # Eski config'i kaldır ve yeniden ekle (her zaman güncelle)
    import re
    html = re.sub(r'<script>window\.__ZEZE_CONFIG__[^<]*</script>', '', html)
    
    if "</head>" in html:
        html = html.replace("</head>", f"  {snippet}\n  </head>", 1)
    else:
        html = snippet + html
    index.write_text(html, encoding="utf-8")


def _frontend_is_stale() -> bool:
    """dist yoksa veya kaynak (src/, config) dist'ten daha yeniyse True.
    Böylece her iyileştirme masaüstünde GARANTİ görünür (eski dist sorunu çözülür)."""
    dist_index = FRONTEND_DIST / "index.html"
    if not dist_index.exists():
        return True
    try:
        dist_mtime = dist_index.stat().st_mtime
        watch_roots = [FRONTEND_DIR / "src"]
        watch_files = [
            FRONTEND_DIR / "index.html",
            FRONTEND_DIR / "package.json",
            FRONTEND_DIR / "vite.config.ts",
            FRONTEND_DIR / "tsconfig.json",
        ]
        newest_src = 0.0
        for root in watch_roots:
            if not root.exists():
                continue
            for dirpath, _dirs, files in os.walk(root):
                for f in files:
                    try:
                        m = os.path.getmtime(os.path.join(dirpath, f))
                        if m > newest_src:
                            newest_src = m
                    except OSError:
                        pass
        for wf in watch_files:
            if wf.exists():
                newest_src = max(newest_src, wf.stat().st_mtime)
        return newest_src > dist_mtime
    except Exception as e:
        log.warning("Staleness check failed (%s); rebuilding to be safe.", e)
        return True


def _ensure_frontend_build() -> bool:
    if not _frontend_is_stale():
        log.info("Frontend dist güncel — derleme atlandı.")
        return True
    log.info("Frontend kaynağı dist'ten yeni → yeniden derleniyor...")
    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    try:
        subprocess.run(
            [npm, "run", "build"],
            cwd=str(FRONTEND_DIR),
            check=True,
            creationflags=CREATE_NO_WINDOW,
        )
        return (FRONTEND_DIST / "index.html").exists()
    except Exception as e:
        log.error("Frontend build failed: %s", e)
        # Eski de olsa mevcut dist'le devam et (tamamen açılmamaktan iyidir)
        return (FRONTEND_DIST / "index.html").exists()


def _another_instance_running() -> bool:
    """Sadece port kontrolÃ¼ - PID tabanlÄ± lock dosyasÄ± yerine."""
    return _port_in_use(BACKEND_PORT) and _port_in_use(UI_PORT)


class ZezelabsDesktopApp:
    def __init__(self):
        self._service_procs: list[dict] = []
        self._rapid_crash_count = 0

    @staticmethod
    def _service_creation_flags() -> int:
        if sys.platform == "win32":
            # DETACHED_PROCESS bazÄ± makinelerde child sÃ¼reÃ§lerin erken sonlanmasÄ±na neden olabiliyor.
            # Konsol gÃ¶stermeden ama sÃ¼reÃ§leri stabil tutacak minimum kombinasyon:
            return CREATE_NO_WINDOW | CREATE_NEW_GROUP
        return 0

    def _start_service(self, role: str, cmd: list[str], cwd: Path | None = None) -> subprocess.Popen:
        log_file = LOG_DIR / "desktop_service.log"
        log_handle = open(log_file, "a", encoding="utf-8")
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd or ROOT),
            env=_desktop_env(),
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            creationflags=self._service_creation_flags(),
            close_fds=False,
        )
        service_info = {
            "role": role,
            "proc": proc,
            "cmd": cmd,
            "started_at": time.time(),
        }
        self._service_procs.append(service_info)
        log.info("Started service role=%s pid=%s cmd=%s", role, proc.pid, cmd[0:4])
        return proc

    def start_ollama(self) -> None:
        if _port_in_use(11434):
            log.info("Ollama port 11434 already in use/running")
            return
        log.info("Starting Ollama service locally...")
        self._start_service(
            "ollama",
            ["ollama", "serve"]
        )

    def start_backend(self) -> None:
        if _port_in_use(BACKEND_PORT):
            log.info("Backend port %s already in use", BACKEND_PORT)
            return
        self._start_service(
            "backend",
            [
                sys.executable,
                "-m",
                "uvicorn",
                "backend.jarvis:app",
                "--host",
                BACKEND_HOST,
                "--port",
                str(BACKEND_PORT),
                "--log-level",
                "info",
            ],
        )

    def start_ui_server(self) -> None:
        if _port_in_use(UI_PORT):
            log.info("UI port %s already in use", UI_PORT)
            return
        if not _ensure_frontend_build():
            raise RuntimeError(
                "ArayÃ¼z derlemesi yok. Bir kez: cd frontend && npm install && npm run build"
            )
        _inject_runtime_config()
        self._start_service(
            "ui",
            [
                sys.executable,
                "-m",
                "http.server",
                str(UI_PORT),
                "--directory",
                str(FRONTEND_DIST),
                "--bind",
                BACKEND_HOST,
            ],
        )

    def open_window(self) -> None:
        url = f"http://{BACKEND_HOST}:{UI_PORT}"
        log.info("Opening UI: %s", url)

        # TarayÄ±cÄ± uygulama modu (Electron'dan daha kararlÄ±; CREATE_NO_WINDOW kullanma)
        edge_paths = [
            Path(os.environ.get("ProgramFiles", "")) / "Microsoft/Edge/Application/msedge.exe",
            Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft/Edge/Application/msedge.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
        ]
        for browser in edge_paths:
            if browser.exists():
                subprocess.Popen(
                    [
                        str(browser),
                        f"--app={url}",
                        "--window-size=1280,800",
                        "--disable-extensions",
                        "--new-window",
                    ],
                    creationflags=CREATE_NEW_GROUP,
                    close_fds=False,
                )
                log.info("Launched browser app mode: %s", browser.name)
                return

        import webbrowser

        webbrowser.open(url)
        log.info("Launched default webbrowser")

    def _kill_other_launcher_instances(self) -> None:
        try:
            import psutil
            current_pid = os.getpid()
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['pid'] == current_pid:
                    continue
                cmdline = proc.info['cmdline']
                if cmdline:
                    cmdline_str = " ".join(cmdline).lower()
                    if "zezelabs_desktop_launcher.py" in cmdline_str:
                        try:
                            log.info(f"Eski launcher sureci sonlandiriliyor: PID {proc.info['pid']}")
                            proc.terminate()
                            proc.wait(timeout=2)
                        except psutil.TimeoutExpired:
                            proc.kill()
                        except Exception as e:
                            log.warning(f"Eski launcher PID {proc.info['pid']} sonlandirilamadi: {e}")
        except Exception as e:
            log.warning(f"Diger launcher instances temizlenirken hata olustu: {e}")

    def _kill_process_on_port(self, port: int) -> None:
        try:
            import psutil
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr.port == port:
                    pid = conn.pid
                    if pid and pid != 0:
                        try:
                            proc = psutil.Process(pid)
                            log.info(f"Port {port} mesgul. PID {pid} ({proc.name()}) sonlandiriliyor...")
                            proc.terminate()
                            proc.wait(timeout=2)
                        except psutil.TimeoutExpired:
                            proc.kill()
                        except Exception as e:
                            log.warning(f"PID {pid} sonlandirilamadi: {e}")
        except Exception as e:
            log.warning(f"Port {port} temizlenirken hata olustu: {e}")

    def run(self) -> int:
        if _another_instance_running():
            log.info("Services already running — opening UI only")
            self.open_window()
            return 0

        log.info("Baslangic temizligi yapiliyor...")
        self._kill_other_launcher_instances()
        self._kill_process_on_port(BACKEND_PORT)
        self._kill_process_on_port(UI_PORT)
        time.sleep(1) # Portlarin serbest kalmasi icin kisa bekleme

        # Portlar temizlendi, baslat
        log.info("Starting services...")

        try:
            self.start_ollama()
            self.start_backend()
            if not _wait_url(f"http://{BACKEND_HOST}:{BACKEND_PORT}/health", timeout=90):
                self._show_error(
                    f"ZOM Ã‡ekirdeÄŸi baÅŸlamadÄ± (port {BACKEND_PORT}).\n"
                    f"Detay: {LOG_FILE}"
                )
                return 1

            self.start_ui_server()
            if not _wait_url(f"http://{BACKEND_HOST}:{UI_PORT}/", timeout=45):
                self._show_error(
                    f"ArayÃ¼z sunucusu baÅŸlamadÄ± (port {UI_PORT}).\n"
                    f"Detay: {LOG_FILE}"
                )
                return 1

            time.sleep(0.5)
            self.open_window()

            # Servisleri ayakta tut â€” pythonw bu dÃ¶ngÃ¼de kalmalÄ±
            while True:
                time.sleep(30)  # 5s â†’ 30s: log spam azaltma, CPU tasarrufu
                for service in list(self._service_procs):
                    proc = service["proc"]
                    code = proc.poll()
                    if code is None:
                        continue

                    role = service["role"]
                    uptime = max(0.0, time.time() - float(service["started_at"]))
                    cmd = service["cmd"]
                    self._service_procs.remove(service)
                    log.warning(
                        "Service exited role=%s pid=%s code=%s uptime=%.1fs cmd=%s",
                        role,
                        proc.pid,
                        code,
                        uptime,
                        cmd[0:4],
                    )

                    if uptime < 15:
                        self._rapid_crash_count += 1
                    else:
                        self._rapid_crash_count = 0

                    if self._rapid_crash_count >= 3:
                        wait_secs = min(90, 10 * self._rapid_crash_count)
                        log.error(
                            "Rapid crash threshold reached (count=%s). Backing off %ss",
                            self._rapid_crash_count,
                            wait_secs,
                        )
                        time.sleep(wait_secs)

                        if self._rapid_crash_count >= 5:
                            self._show_error(
                                "ZOM servisleri art arda Ã§Ã¶kÃ¼yor. Otomatik yeniden baÅŸlatma durduruldu.\n"
                                f"LÃ¼tfen loglarÄ± kontrol edin: {LOG_FILE}"
                            )
                            return 1

                    if role == "backend":
                        if code not in (0, None) and code != 4294967295:
                            log.error("Backend exited with fatal code=%s. Not restarting automatically.", code)
                            self._show_error(
                                "Backend beklenmeyen bir hata ile kapandÄ±.\n"
                                f"Kod: {code}\nLog: {LOG_FILE}"
                            )
                            return 1
                        if not _port_in_use(BACKEND_PORT):
                            self.start_backend()
                    elif role == "ui":
                        if code not in (0, None) and code != 4294967295:
                            log.error("UI service exited with fatal code=%s. Not restarting automatically.", code)
                            self._show_error(
                                "ArayÃ¼z servisi beklenmeyen bir hata ile kapandÄ±.\n"
                                f"Kod: {code}\nLog: {LOG_FILE}"
                            )
                            return 1
                        if not _port_in_use(UI_PORT):
                            self.start_ui_server()

                # Harici sÃ¼reÃ§ler portlarÄ± ayaÄŸa kaldÄ±rdÄ±ysa rapid crash sayacÄ±nÄ± sÄ±fÄ±rla
                if _port_in_use(BACKEND_PORT) and _port_in_use(UI_PORT):
                    self._rapid_crash_count = 0
        except Exception as e:
            log.exception("Launcher crash: %s", e)
            self._show_error(f"Beklenmeyen hata:\n{e}\n\nLog: {LOG_FILE}")
            return 1
        finally:
            log.info("Temizlik baslatiliyor: Arka plan servisleri kapatiliyor...")
            for service in list(self._service_procs):
                proc = service["proc"]
                role = service["role"]
                if proc.poll() is None:
                    log.info(f"Servis sonlandiriliyor: {role} (PID: {proc.pid})")
                    try:
                        proc.terminate()
                        proc.wait(timeout=3)
                    except Exception:
                        try:
                            proc.kill()
                        except Exception:
                            pass
            self._service_procs.clear()
            # Herhangi bir Ollama işlemini durdur
            self._kill_ollama_processes()
            # Lock dosyasini temizle
            try:
                LOCK_FILE.unlink(missing_ok=True)
            except OSError:
                pass

    def _kill_ollama_processes(self) -> None:
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name']):
                name = proc.info['name'].lower()
                if "ollama" in name:
                    try:
                        log.info(f"Ollama sureci sonlandiriliyor: PID {proc.info['pid']} ({proc.info['name']})")
                        proc.kill()
                    except Exception as e:
                        log.warning(f"Ollama sureci {proc.info['pid']} sonlandirilamadi: {e}")
        except Exception as e:
            log.warning(f"Ollama surecleri temizlenirken hata: {e}")

    @staticmethod
    def _show_error(msg: str) -> None:
        log.error(msg)
        if sys.platform == "win32":
            try:
                import ctypes

                ctypes.windll.user32.MessageBoxW(0, msg, "Zezelabs ZOM", 0x10)
            except Exception:
                pass


def main() -> int:
    os.chdir(ROOT)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    
    # BaÅŸlangÄ±Ã§ta eski lock dosyalarÄ±nÄ± temizle
    try:
        LOCK_FILE.unlink(missing_ok=True)
    except OSError:
        pass
    
    return ZezelabsDesktopApp().run()


if __name__ == "__main__":
    raise SystemExit(main())

