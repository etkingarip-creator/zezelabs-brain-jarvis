import pytest
import asyncio
import os
import sys
import uuid
import pathlib

# Prevent Heavy Imports during test
sys.modules['edge_tts'] = type('MockEdgeTTS', (), {})()
sys.modules['sounddevice'] = type('MockSD', (), {})()
sys.modules['silero_vad'] = type('MockSilero', (), {})()
sys.modules['faster_whisper'] = type('MockWhisper', (), {})()

from backend.jarvis import app, TaskRequest, post_task

def test_hybrid_task_e2e(monkeypatch):
    monkeypatch.setenv("ZOM_AI_MODE", "hybrid_deepseek_hermes")
    monkeypatch.setenv("ZOM_ENABLE_HERMES_SYNC", "false")
    monkeypatch.setenv("ZOM_ENABLE_OLLAMA_FALLBACK", "false")
    monkeypatch.setenv("ZOM_MOCK_DEEPSEEK", "true")
    monkeypatch.setenv("ZOM_ENABLE_CLAWDE_OPERATOR", "true")
    
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "workspace"))
    monkeypatch.setenv("WORKSPACE_DIR", workspace_dir)

    req = TaskRequest(task="workspace içinde hello_from_hybrid.txt oluştur", dry_run=True)
    
    # Needs to be called via asyncio.run since it's an async FastAPI route
    res = asyncio.run(post_task(req))
    
    assert res.get("success") is True
    assert "task_id" in res
    assert res.get("provider_mode") == "hybrid_deepseek_hermes"
    assert res.get("degraded_mode") is True
    
    files = res.get("created_files", [])
    assert len(files) == 1
    assert "hello_from_hybrid.txt" in files[0]
    assert "hybrid_tasks" in files[0]
    
    path = pathlib.Path(files[0])
    assert path.exists(), f"File was not created at {path}"
    content = path.read_text(encoding="utf-8")
    assert "Hello from Hybrid Jarvis" in content
    
    
    guard = res.get("zeze_guard", {})
    assert guard.get("roi_recorded") is True
    assert guard.get("loop_recorded") is True

def test_hybrid_task_denies_path_traversal(monkeypatch):
    monkeypatch.setenv("ZOM_AI_MODE", "hybrid_deepseek_hermes")
    monkeypatch.setenv("ZOM_ENABLE_HERMES_SYNC", "false")
    monkeypatch.setenv("ZOM_ENABLE_OLLAMA_FALLBACK", "false")
    monkeypatch.setenv("ZOM_MOCK_DEEPSEEK", "true")
    monkeypatch.setenv("ZOM_ENABLE_CLAWDE_OPERATOR", "true")
    
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "workspace"))
    monkeypatch.setenv("WORKSPACE_DIR", workspace_dir)

    req = TaskRequest(task="workspace dışında ../evil.txt oluştur", dry_run=True)
    res = asyncio.run(post_task(req))
    
    assert res.get("success") is False
    assert len(res.get("created_files", [])) == 0
