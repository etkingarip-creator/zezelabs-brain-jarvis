import pytest
import sys

# Prevent Heavy Imports during test
sys.modules['edge_tts'] = type('MockEdgeTTS', (), {})()
sys.modules['sounddevice'] = type('MockSD', (), {})()
sys.modules['silero_vad'] = type('MockSilero', (), {})()
sys.modules['faster_whisper'] = type('MockWhisper', (), {})()

from fastapi.testclient import TestClient
from backend.jarvis import app

@pytest.fixture
def client():
    return TestClient(app)

def test_jarvis_chat_endpoint(client, monkeypatch):
    monkeypatch.setenv("ZOM_AI_MODE", "mock_mode")
    payload = {"message": "Merhaba Jarvis!"}
    response = client.post("/api/jarvis/chat", json=payload)
    
    assert response.status_code == 200
    resp_data = response.json()
    assert "response" in resp_data
    assert "status" in resp_data
    assert resp_data["status"] == "success"

def test_department_status_endpoint(client):
    # Test a valid department (zeze_eng)
    response = client.get("/api/departments/zeze_eng/status")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "uptime" in data
    assert "queue_depth" in data
    
    # Verify the overhauled dynamic audit parameters are populated correctly
    assert "audit" in data
    audit = data["audit"]
    assert "rabbitmq_connection" in audit
    assert "config_status" in audit
    assert "issues" in audit
    assert "workload" in audit
    assert audit["config_status"] == "OK"

def test_invalid_department_status(client):
    response = client.get("/api/departments/invalid_dept/status")
    assert response.status_code == 404
