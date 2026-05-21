import os
import uuid
import pytest
from departments.media_factory.agent import MediaFactoryAgent
from core.orchestrator.router_agent import RouterAgent
from core.zeze_guard.storage import get_storage
from live_matrix.backend.zeze_guard_provider import ZezeGuardProvider

WORKSPACE = os.path.abspath(".")

@pytest.fixture(autouse=True)
def reset_storage():
    get_storage().clear()
    yield
    get_storage().clear()

def test_media_factory_agent_tasks():
    agent = MediaFactoryAgent(workspace_root=WORKSPACE)
    
    # 2. run_video_task
    res_video = agent.run_video_task("youtube videosu")
    assert res_video.success is True
    assert any("video_brief.md" in f for f in res_video.tool_results[0]["files_created"])
    assert any("script.md" in f for f in res_video.tool_results[0]["files_created"])
    
    # 3. run_seo_task
    res_seo = agent.run_seo_task("seo uyumlu makale")
    assert res_seo.success is True
    assert any("seo_report.md" in f for f in res_seo.tool_results[0]["files_created"])
    assert any("keywords.json" in f for f in res_seo.tool_results[0]["files_created"])
    
    # 4. run_content_task
    res_content = agent.run_content_task("icerik takvimi")
    assert res_content.success is True
    assert any("content_calendar.md" in f for f in res_content.tool_results[0]["files_created"])
    
    # 5. run_thumbnail_task
    res_thumb = agent.run_thumbnail_task("thumbnail tasarimi")
    assert res_thumb.success is True
    assert any("thumbnail_brief.md" in f for f in res_thumb.tool_results[0]["files_created"])
    
    # 6. run_distribution_plan_task
    res_dist = agent.run_distribution_plan_task("dagitim plani")
    assert res_dist.success is True
    assert any("distribution_plan.md" in f for f in res_dist.tool_results[0]["files_created"])

    # 16-22. Policy checks
    checks = res_video.tool_results[0]["policy_checks"]
    assert checks["external_publish_requires_approval"] is True
    assert checks["youtube_upload_requires_approval"] is True
    assert checks["paid_ads_launch_requires_approval"] is True
    assert checks["live_trade_denied"] is True
    assert checks["deploy_denied"] is True
    assert checks["git_push_denied"] is True

def test_media_factory_guard_integration():
    agent = MediaFactoryAgent(workspace_root=WORKSPACE)
    task_id = str(uuid.uuid4())
    
    # trigger loop
    agent.run_video_task("video", task_id)
    agent.run_video_task("video", task_id)
    agent.run_video_task("video", task_id)
    
    provider = ZezeGuardProvider()
    snap = provider.get_zeze_guard_snapshot()
    
    # 14. ROITracker
    assert snap["roi"]["total_cost_usd"] > 0
    # 15. AntiLoopEngine
    assert snap["anti_loop"]["active_loops"] == 1
    assert any("media_factory" in alert["title"] for alert in snap["alerts"])

def test_router_mapping():
    # 23. Router mapping
    router = RouterAgent(None)
    assert router._determine_agent("youtube videosu çek") == "zeze_media"
    assert router._determine_agent("seo calismasi") == "zeze_media"
    assert router._determine_agent("content uret") == "zeze_media"
