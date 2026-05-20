import pytest
from core.zeze_guard.shadow_ceo_alerts import ShadowCEOAlertClient
from core.zeze_guard.storage import get_storage

@pytest.fixture(autouse=True)
def reset_storage():
    get_storage().clear()
    yield

def test_mock_telegram_alert_sent():
    client = ShadowCEOAlertClient()
    res = client.send_alert("Loop Detected", "Agent is stuck", "critical", {"task": "123"})
    
    assert res["sent"] is True
    assert res["channel"] == "mock_telegram"
    assert res["severity"] == "critical"
    
    # Storage check
    alerts = get_storage().alerts
    assert len(alerts) == 1
    assert alerts[0]["title"] == "Loop Detected"
    assert alerts[0]["severity"] == "critical"
    assert alerts[0]["metadata"]["task"] == "123"
