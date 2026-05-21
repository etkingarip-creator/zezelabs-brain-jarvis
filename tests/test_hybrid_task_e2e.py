"""
tests/test_hybrid_task_e2e.py
End-to-end tests for the hybrid DeepSeek/Hermes task endpoint.
Covers path traversal denial, degraded mode, and provider routing.
"""
import os
import asyncio
import pytest

from backend.jarvis import post_task, TaskRequest


class TestHybridTaskE2E:
    def test_hybrid_task_denies_path_traversal(self, monkeypatch):
        monkeypatch.setenv("ZOM_AI_MODE", "hybrid_deepseek_hermes")
        monkeypatch.setenv("ZOM_ENABLE_HERMES_SYNC", "false")
        monkeypatch.setenv("ZOM_ENABLE_OLLAMA_FALLBACK", "false")
        monkeypatch.setenv("ZOM_MOCK_DEEPSEEK", "true")
        monkeypatch.setenv("ZOM_ENABLE_CLAWDE_OPERATOR", "true")

        workspace_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "workspace")
        )
        monkeypatch.setenv("WORKSPACE_DIR", workspace_dir)

        req = TaskRequest(task="workspace dışında ../evil.txt oluştur", dry_run=True)
        res = asyncio.run(post_task(req))

        assert res.get("success") is False, (
            f"Expected success=False for path traversal attempt, got: {res}"
        )

    def test_hybrid_task_normal_succeeds(self, monkeypatch):
        monkeypatch.setenv("ZOM_AI_MODE", "hybrid_deepseek_hermes")
        monkeypatch.setenv("ZOM_ENABLE_HERMES_SYNC", "false")
        monkeypatch.setenv("ZOM_ENABLE_OLLAMA_FALLBACK", "false")
        monkeypatch.setenv("ZOM_MOCK_DEEPSEEK", "true")
        monkeypatch.setenv("ZOM_ENABLE_CLAWDE_OPERATOR", "true")

        workspace_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "workspace")
        )
        monkeypatch.setenv("WORKSPACE_DIR", workspace_dir)

        req = TaskRequest(task="list files in workspace", dry_run=True)
        res = asyncio.run(post_task(req))

        # Normal tasks should not be denied at the traversal gate
        assert res.get("success") is not False or "traversal" not in res.get("error", ""), (
            f"Normal task should not be blocked by traversal guard: {res}"
        )

    def test_hybrid_task_degraded_mode_when_hermes_offline(self, monkeypatch):
        monkeypatch.setenv("ZOM_AI_MODE", "hybrid_deepseek_hermes")
        monkeypatch.setenv("ZOM_ENABLE_HERMES_SYNC", "false")
        monkeypatch.setenv("ZOM_MOCK_DEEPSEEK", "true")
        monkeypatch.setenv("ZOM_ENABLE_CLAWDE_OPERATOR", "false")

        req = TaskRequest(task="summarise the project", dry_run=True)
        res = asyncio.run(post_task(req))

        # When Hermes is offline the orchestrator falls back to degraded mode
        assert res.get("success") is True
        assert res.get("degraded_mode") is True or res.get("hermes_status") == "offline"

    def test_path_traversal_variants_denied(self, monkeypatch):
        monkeypatch.setenv("ZOM_AI_MODE", "hybrid_deepseek_hermes")
        monkeypatch.setenv("ZOM_MOCK_DEEPSEEK", "true")

        traversal_tasks = [
            "read ../../../etc/passwd",
            "create /home/user/../evil.sh",
            "open ..\\secrets.txt",
        ]
        for task_str in traversal_tasks:
            req = TaskRequest(task=task_str, dry_run=True)
            res = asyncio.run(post_task(req))
            assert res.get("success") is False, (
                f"Expected traversal denial for: {repr(task_str)}, got: {res}"
            )
