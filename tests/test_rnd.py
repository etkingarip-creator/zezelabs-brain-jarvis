import pytest

@pytest.mark.anyio
async def test_trend_scout():
    from core.ai.providers.trend_scout import TrendScout
    scout = TrendScout()
    result = await scout.scan()
    assert isinstance(result, list)
    assert len(result) > 0
    assert "title" in result[0]

@pytest.mark.anyio
async def test_sandbox_engineer():
    from core.ai.providers.sandbox_engineer import SandboxEngineer
    engineer = SandboxEngineer()
    result = await engineer.test({"title": "Kokoro-TTS", "score": 0.95})
    assert result["passed"] is True
    assert result["latency_ms"] == 45
    assert result["memory_mb"] == 120

@pytest.mark.anyio
async def test_injector():
    from core.ai.providers.injector import Injector
    injector = Injector()
    result = await injector.inject({"title": "Kokoro-TTS"})
    assert "branch" in result
    assert result["status"] == "ready"

@pytest.mark.anyio
async def test_rnd_agent_cycle():
    from departments.zeze_rnd.agent import ZezeRndAgent
    agent = ZezeRndAgent()
    result = await agent.run_cycle()
    assert "trend" in result
    assert "sandbox" in result
    assert "injection" in result
    assert result["sandbox"]["passed"] is True
    assert "branch" in result["injection"]
