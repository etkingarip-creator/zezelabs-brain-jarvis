import pytest
import asyncio
from core.ai.provider_sync import ProviderSyncOrchestrator
from core.operator_runtime.clawde_kernel import ToolRequest

def test_provider_sync_init():
    orchestrator = ProviderSyncOrchestrator()
    assert orchestrator.get_mode() == "hybrid_deepseek_hermes"
    
def test_hermes_offline_degraded(monkeypatch):
    monkeypatch.setenv("ZOM_ENABLE_HERMES_SYNC", "true")
    orchestrator = ProviderSyncOrchestrator()
    
    plan = {"plan": {"action": "execute", "details": "test"}}
    res = asyncio.run(orchestrator.execute_with_hermes(plan))
    assert res.get("hermes_status") == "offline"
    assert res.get("degraded_mode") is True

def test_deepseek_mock_plan(monkeypatch):
    monkeypatch.setenv("ZOM_MOCK_DEEPSEEK", "true")
    orchestrator = ProviderSyncOrchestrator()
    res = asyncio.run(orchestrator.plan_with_deepseek("test"))
    assert res["plan_status"] == "success"
    assert "mock_deepseek" in res["provider"]

def test_execute_with_clawde():
    orchestrator = ProviderSyncOrchestrator()
    plan = {"plan": {"action": "execute", "details": "test.txt"}}
    res = asyncio.run(orchestrator.execute_with_clawde(plan))
    assert res["executor"] == "clawde"
    assert "execution_status" in res
