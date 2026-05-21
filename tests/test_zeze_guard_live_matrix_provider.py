import pytest
from fastapi.testclient import TestClient
from live_matrix.backend.zeze_guard_provider import ZezeGuardProvider
from live_matrix.backend.api import app
from core.zeze_guard.storage import get_storage
from core.zeze_guard.anti_loop import AntiLoopEngine
from core.zeze_guard.roi_tracker import ROITracker
from core.zeze_guard.shadow_ceo_alerts import ShadowCEOAlertClient

@pytest.fixture(autouse=True)
def reset_storage_and_seed():
    storage = get_storage()
    storage.clear()
    
    # Seed data
    AntiLoopEngine().record_event("ag_1", "t_1", "err", "sig1")
    AntiLoopEngine().record_event("ag_1", "t_1", "err", "sig1")
    AntiLoopEngine().record_event("ag_1", "t_1", "err", "sig1")
    
    ROITracker().record_cost("ag_1", "t_1", "model", 100, 100, 1.5)
    ROITracker().record_outcome("ag_1", "t_1", "task", True)
    
    ShadowCEOAlertClient().send_alert("Test Alert", "msg")
    
    yield
    storage.clear()

def test_provider_snapshot():
    provider = ZezeGuardProvider()
    snap = provider.get_zeze_guard_snapshot()
    
    assert "anti_loop" in snap
    assert "roi" in snap
    assert "alerts" in snap
    
    assert snap["anti_loop"]["active_loops"] == 1
    assert len(snap["anti_loop"]["freeze_recommendations"]) == 1
    
    assert snap["roi"]["total_cost_usd"] == 1.5
    assert snap["roi"]["successful_tasks"] == 1
    
    assert len(snap["alerts"]) == 1

def test_fastapi_endpoints():
    client = TestClient(app)
    
    res = client.get("/api/zeze-guard/snapshot")
    assert res.status_code == 200
    assert res.json()["anti_loop"]["active_loops"] == 1
    
    res = client.get("/api/zeze-guard/loops")
    assert res.status_code == 200
    
    res = client.get("/api/zeze-guard/roi")
    assert res.status_code == 200
    
    res = client.get("/api/zeze-guard/alerts")
    assert res.status_code == 200
