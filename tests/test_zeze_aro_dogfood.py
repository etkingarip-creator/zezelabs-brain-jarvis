import os
import uuid
import pytest
from departments.zeze_aro.agent import ZezeAroAgent
from core.orchestrator.router_agent import RouterAgent
from core.zeze_guard.storage import get_storage
from live_matrix.backend.zeze_guard_provider import ZezeGuardProvider

WORKSPACE = os.path.abspath(".")

@pytest.fixture(autouse=True)
def reset_storage():
    get_storage().clear()
    yield
    get_storage().clear()

def test_zeze_aro_agent_tasks():
    agent = ZezeAroAgent(workspace_root=WORKSPACE)
    
    # run sales
    res_sales = agent.run_sales_task("satis yap")
    assert res_sales.success is True
    assert "sales_report.md" in res_sales.tool_results[0]["files_created"][0]
    
    # run marketing
    res_marketing = agent.run_marketing_task("pazarlama yap")
    assert res_marketing.success is True
    
    # run crm
    res_crm = agent.run_crm_task("crm guncelle")
    assert res_crm.success is True
    
    # check files
    state_dir = os.path.join(WORKSPACE, "zeze_aro", "dogfood_reports")
    assert os.path.exists(os.path.join(state_dir, "sales_report.md"))
    assert os.path.exists(os.path.join(state_dir, "sales_report.json"))
    
    # check policy
    checks = res_sales.tool_results[0]["policy_checks"]
    assert checks["git_push_denied"] is True
    assert checks["deploy_denied"] is True
    assert checks["live_trade_denied"] is True

def test_zeze_aro_guard_integration():
    agent = ZezeAroAgent(workspace_root=WORKSPACE)
    task_id = str(uuid.uuid4())
    
    # trigger loop
    agent.run_sales_task("satis", task_id)
    agent.run_sales_task("satis", task_id)
    agent.run_sales_task("satis", task_id)
    
    provider = ZezeGuardProvider()
    snap = provider.get_zeze_guard_snapshot()
    
    assert snap["roi"]["total_cost_usd"] > 0
    assert snap["anti_loop"]["active_loops"] == 1
    assert any("zeze_aro" in alert["title"] for alert in snap["alerts"])
    assert "zeze_aro_agent" in snap["roi"]["agents"]

def test_router_mapping():
    router = RouterAgent(None)
    assert router._determine_agent("sales funnel olustur") == "zeze_aro"
    assert router._determine_agent("marketing campaign ads") == "zeze_aro"
