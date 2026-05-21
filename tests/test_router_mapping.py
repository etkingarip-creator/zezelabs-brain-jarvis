"""
tests/test_router_mapping.py
RouterAgent — department mapping tests with extended keyword set
"""
import asyncio
import pytest
from core.orchestrator.router_agent import RouterAgent


class DummyMQ:
    def __init__(self):
        self.log = []
    def publish(self, queue, payload):
        self.log.append(queue)
        return True


def route(desc):
    mq = DummyMQ()
    router = RouterAgent(mq)
    result = asyncio.run(router.route_task(desc, {}))
    return result.get("agent"), result.get("status")


class TestRouterMapping:
    def test_code_task_goes_to_eng(self):
        agent, status = route("kod yaz backend için")
        assert agent == "eng"
        assert status == "dispatched"

    def test_bug_fix_goes_to_eng(self):
        agent, _ = route("bu bug'ı fix et")
        assert agent == "eng"

    def test_deploy_goes_to_eng(self):
        agent, _ = route("deploy yap production'a")
        assert agent == "eng"

    def test_video_goes_to_media(self):
        agent, _ = route("youtube videosu hazırla")
        assert agent == "media"

    def test_seo_goes_to_media(self):
        agent, _ = route("SEO raporu çıkar")
        assert agent == "media"

    def test_education_goes_to_academy(self):
        agent, _ = route("egitim icerigi olustur")
        assert agent == "academy"

    def test_strategy_goes_to_mystic(self):
        agent, _ = route("strateji planı hazırla")
        assert agent == "mystic"

    def test_roadmap_goes_to_mystic(self):
        agent, _ = route("roadmap çıkar Q3 için")
        assert agent == "mystic"

    def test_btc_goes_to_fin(self):
        agent, _ = route("BTC fiyatini takip et")
        assert agent == "crypto"

    def test_budget_report_goes_to_fin(self):
        agent, _ = route("butce raporu hazirla")
        assert agent == "crypto"

    def test_sales_goes_to_aro(self):
        agent, _ = route("satis kampanyasi planla")
        assert agent == "zeze_aro"

    def test_marketing_goes_to_aro(self):
        agent, _ = route("marketing planı oluştur")
        assert agent == "zeze_aro"

    def test_telegram_goes_to_telegram(self):
        agent, _ = route("telegram'a bildirim gönder")
        assert agent == "telegram"

    def test_unknown_goes_to_general(self):
        agent, _ = route("hava durumu nedir")
        assert agent == "general"

    def test_task_id_is_uuid(self):
        mq = DummyMQ()
        router = RouterAgent(mq)
        result = asyncio.run(router.route_task("kod yaz", {}))
        assert len(result.get("task_id", "")) == 36

    def test_dlq_on_publish_failure(self):
        class FailMQ:
            def __init__(self):
                self.log = []
            def publish(self, queue, payload):
                if queue != "zom_dead_letter_queue":
                    self.log.append((queue, "FAIL"))
                    return False
                self.log.append((queue, "DLQ_OK"))
                return True

        mq = FailMQ()
        router = RouterAgent(mq)
        result = asyncio.run(router.route_task("kod yaz", {}))
        assert result.get("status") == "error"
        assert any("zom_dead_letter_queue" in e[0] for e in mq.log)
