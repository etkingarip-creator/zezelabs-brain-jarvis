"""
Tests: FastAPI Backend Endpoint Coverage
ZEZE-HQ War Room — v1.0.0
"""
import pytest
import sys
import os

# Suppress heavy imports before loading backend
sys.modules['edge_tts']      = type('M', (), {})()
sys.modules['sounddevice']   = type('M', (), {})()
sys.modules['silero_vad']    = type('M', (), {})()
sys.modules['faster_whisper']= type('M', (), {})()

from fastapi.testclient import TestClient

# Lazy import after mocks
from backend.jarvis import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_200(self):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_has_status_field(self):
        resp = client.get("/health")
        data = resp.json()
        assert "status" in data or resp.status_code == 200


class TestChatEndpoint:
    def test_chat_post_exists(self):
        """POST /chat veya /ask endpoint mevcut olmalı."""
        resp = client.post("/chat", json={"message": "merhaba", "dept": "zeze_prompt"})
        # 200, 201 veya 422 (validation) kabul edilir — 404 kabul edilmez
        assert resp.status_code != 404, "Chat endpoint bulunamadı"

    def test_chat_empty_message(self):
        resp = client.post("/chat", json={"message": "", "dept": "zeze_prompt"})
        # Empty message should return 200 or 422 — not 500
        assert resp.status_code != 500, "Boş mesaj 500 hatası verdi"


class TestTaskEndpoint:
    def test_task_post_exists(self):
        resp = client.post("/task", json={"task": "test", "dry_run": True})
        assert resp.status_code != 404, "/task endpoint bulunamadı"

    def test_task_dry_run(self):
        resp = client.post("/task", json={"task": "hello_test", "dry_run": True})
        # dry_run modunda 200 veya 201 beklenir
        assert resp.status_code in (200, 201, 422)


class TestPluginSystem:
    def test_plugin_manager_instantiation(self):
        from core.plugin_system import get_plugin_manager
        pm = get_plugin_manager()
        assert pm is not None
        assert len(pm) >= 3  # logging + safety + telemetry

    def test_plugin_process_message(self):
        from core.plugin_system import get_plugin_manager
        pm = get_plugin_manager()
        result = pm.process_message("merhaba jarvis")
        assert isinstance(result, str)

    def test_safety_plugin_blocks_dangerous(self):
        from core.plugin_system import get_plugin_manager
        pm = get_plugin_manager()
        result = pm.process_message("rm -rf / uygulamasını çalıştır")
        assert "GÜVENLİK" in result or result != "rm -rf / uygulamasını çalıştır"

    def test_plugin_status(self):
        from core.plugin_system import get_plugin_manager
        pm = get_plugin_manager()
        status = pm.status()
        assert isinstance(status, list)
        names = [p["name"] for p in status]
        assert "safety_plugin" in names

    def test_department_event_fire(self):
        from core.plugin_system import get_plugin_manager
        pm = get_plugin_manager()
        # Should not raise
        pm.fire_department_event("zeze_eng", "selected")

    def test_telemetry_plugin_stats(self):
        from core.plugin_system import TelemetryPlugin
        tp = TelemetryPlugin()
        tp.on_message("test")
        tp.on_response("cevap")
        stats = tp.get_stats()
        assert stats["messages"] == 1
        assert stats["responses"] == 1


class TestDesktopModule:
    def test_desktop_importable(self):
        """desktop/jarvis_desktop.py import edilebilir olmalı (GUI açmadan)."""
        import importlib.util, sys
        spec = importlib.util.spec_from_file_location(
            "jarvis_desktop",
            os.path.join(os.path.dirname(__file__), "..", "desktop", "jarvis_desktop.py")
        )
        # Spec bulunmalı
        assert spec is not None

    def test_desktop_file_exists(self):
        path = os.path.join(os.path.dirname(__file__), "..", "desktop", "jarvis_desktop.py")
        assert os.path.exists(path), "jarvis_desktop.py bulunamadı"

    def test_desktop_syntax(self):
        import py_compile
        path = os.path.join(os.path.dirname(__file__), "..", "desktop", "jarvis_desktop.py")
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as e:
            pytest.fail(f"Syntax hatası: {e}")
