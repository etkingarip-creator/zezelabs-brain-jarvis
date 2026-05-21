import os
import pytest

def test_mock_provider_returns_response():
    os.environ["ZOM_MOCK_DEEPSEEK"] = "true"
    from core.ai.providers.deepseek import DeepSeekProvider
    provider = DeepSeekProvider()
    response = provider.complete("Hello")
    assert "Mock response" in response

def test_health_check_mock():
    os.environ["ZOM_MOCK_DEEPSEEK"] = "true"
    from core.ai.providers.deepseek import DeepSeekProvider
    provider = DeepSeekProvider()
    health = provider.health_check()
    assert health["status"] == "mock"

def test_real_mode_skips_without_key():
    os.environ["ZOM_MOCK_DEEPSEEK"] = "false"
    old_key = os.environ.pop("DEEPSEEK_API_KEY", None)
    try:
        from core.ai.providers.deepseek import DeepSeekProvider
        provider = DeepSeekProvider()
        assert provider.mock is True  # Falls back to mock
    finally:
        if old_key is not None:
            os.environ["DEEPSEEK_API_KEY"] = old_key

def test_invalid_key_raises():
    os.environ["ZOM_MOCK_DEEPSEEK"] = "false"
    old_key = os.environ.get("DEEPSEEK_API_KEY")
    os.environ["DEEPSEEK_API_KEY"] = "invalid"
    try:
        from core.ai.providers.deepseek import DeepSeekProvider
        provider = DeepSeekProvider(api_key="invalid")
        with pytest.raises(Exception) as exc_info:
            import asyncio
            asyncio.run(provider.complete_async("test"))
        assert "Invalid API key" in str(exc_info.value)
    finally:
        if old_key is not None:
            os.environ["DEEPSEEK_API_KEY"] = old_key
        else:
            os.environ.pop("DEEPSEEK_API_KEY", None)
