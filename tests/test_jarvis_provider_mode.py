import pytest
import asyncio
import os
import sys

# Prevent Heavy Imports during test
import sys
sys.modules['edge_tts'] = type('MockEdgeTTS', (), {})()
sys.modules['sounddevice'] = type('MockSD', (), {})()
sys.modules['silero_vad'] = type('MockSilero', (), {})()
sys.modules['faster_whisper'] = type('MockWhisper', (), {})()

from backend.jarvis import Brain

def test_jarvis_provider_mode(monkeypatch):
    monkeypatch.setenv("ZOM_AI_MODE", "hybrid_deepseek_hermes")
    monkeypatch.setenv("ZOM_ENABLE_HERMES_SYNC", "false")
    monkeypatch.setenv("ZOM_ENABLE_OLLAMA_FALLBACK", "false")
    monkeypatch.setenv("ZOM_MOCK_DEEPSEEK", "true")

    brain = Brain()
    res = asyncio.run(brain.think("test prompt"))
    
    # In hybrid mode without hermes, it degrades to deepseek mock
    assert "MOCK_DEEPSEEK" in res or "mock_deepseek" in res.lower() or "Hybrid Execution Plan" in res
