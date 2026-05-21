import pytest
from fastapi.testclient import TestClient
from backend.jarvis import app

@pytest.fixture
def client():
    return TestClient(app)

def test_hsl_to_hex():
    from desktop.theme.colors import hsl_to_hex
    assert hsl_to_hex(210, 80, 50) == "#4da6ff"

def test_theme_loaded():
    from desktop.theme.colors import get_theme
    theme = get_theme()
    assert "background" in theme
    assert theme["background"] == "#0f172a"

def test_sse_endpoint(client):
    response = client.get("/api/runtime/streamlogs")
    assert response.status_code == 200
