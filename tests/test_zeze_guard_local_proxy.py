import pytest
from core.zeze_guard.local_proxy import LocalFirstProxy

def test_api_key_redaction():
    proxy = LocalFirstProxy()
    assert proxy.redact_secrets("my key is sk-12345") == "my key is ***-12345"

def test_token_estimation():
    proxy = LocalFirstProxy()
    # 20 chars ~ 5 tokens
    assert proxy.estimate_tokens("12345678901234567890") == 5

def test_route_model():
    proxy = LocalFirstProxy()
    assert proxy.route_model("openrouter", "any-model") == "deepseek/deepseek-coder"
    assert proxy.route_model("openai", "gpt-4") == "gpt-4"

def test_cache_decision():
    proxy = LocalFirstProxy()
    assert proxy.should_cache("please cache_me this") is True
    assert proxy.should_cache("do something else") is False
