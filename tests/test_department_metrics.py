import pytest
from fastapi.testclient import TestClient
from backend.jarvis import app

@pytest.fixture
def client():
    return TestClient(app)

def test_invalid_department(client):
    response = client.get("/api/departments/invalid_dept/status")
    assert response.status_code == 404

def test_all_department_status_keys(client):
    valid_departments = [
        "zeze_prompt", "zeze_guard", "zeze_sec", "zeze_rnd", 
        "zeze_eng", "crypto_trading", "media_factory", "app_factory", "zeze_aro"
    ]
    
    for dept in valid_departments:
        response = client.get(f"/api/departments/{dept}/status")
        assert response.status_code == 200
        data = response.json()
        
        # Verify mandatory visual fields exist
        assert "status" in data
        assert "uptime" in data
        assert "api_calls" in data
        assert "success_rate" in data
        assert "system_usage" in data
        assert "active_agents" in data
        assert "agents_list" in data
        
        # Check system usage parameters
        usage = data["system_usage"]
        assert "cpu" in usage
        assert "ram" in usage
        assert "gpu" in usage
        
        # Verify robust audit diagnostic fields
        assert "audit" in data
        audit = data["audit"]
        assert "rabbitmq_connection" in audit
        assert "config_status" in audit
        assert "issues" in audit
        assert "workload" in audit
        
        # For zeze_eng, verify that it carries specific warning strings under critical workload
        if dept == "zeze_eng":
            assert data["status"] in ["MEŞGUL", "AKTİF", "TARANIYOR"]
            assert audit["rabbitmq_connection"] in ["CONNECTED", "FALLBACK_ACTIVE"]
