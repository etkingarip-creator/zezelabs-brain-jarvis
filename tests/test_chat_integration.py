import pytest
from fastapi.testclient import TestClient
from backend.jarvis import app

@pytest.fixture
def client():
    return TestClient(app)

def test_chat_invalid_payload(client):
    # Empty message should return 422 validation error
    response = client.post("/api/jarvis/chat", json={})
    assert response.status_code == 422

def test_chat_empty_message(client):
    # Empty string should fail with 400 Bad Request
    response = client.post("/api/jarvis/chat", json={"message": ""})
    assert response.status_code == 400
    assert "message is required" in response.json()["detail"]

def test_chat_valid_response(client):
    # A valid message should return a JSON response with status 'success' and a reply response string
    response = client.post("/api/jarvis/chat", json={"message": "Merhaba Jarvis!"})
    assert response.status_code == 200
    resp_data = response.json()
    assert "response" in resp_data
    assert resp_data["status"] == "success"
    # Ensure it welcomingly references Zezelabs or the command center
    assert "Zezelabs" in resp_data["response"]
