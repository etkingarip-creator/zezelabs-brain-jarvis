"""
FULL AUTONOMOUS ORCHESTRATION DRY-RUN
Requires no Docker, no RabbitMQ, no external API.
Run: python dry_run_test.py
"""
import asyncio
import logging
logging.basicConfig(level=logging.WARNING)

from core.orchestrator.router_agent import RouterAgent


# ── DRY-RUN DummyMQ ──────────────────────────────────────────────────
class DummyMQ:
    def __init__(self):
        self.log = []

    def publish(self, queue_name, payload):
        self.log.append((queue_name, payload.get("task_id", "?")))
        return True  # always succeeds


class FailMQ(DummyMQ):
    """Simulates a publish failure to test DLQ fallback path."""
    def publish(self, queue_name, payload):
        if queue_name != "zom_dead_letter_queue":
            self.log.append((queue_name, payload.get("task_id", "?"), "FAIL"))
            return False
        self.log.append((queue_name, payload.get("task_id", "?"), "DLQ_OK"))
        return True


# ── TEST CASES (task_description, expected_agent) ─────────────────────
CASES = [
    # Engineering
    ("kod yaz backend için",                    "eng"),
    ("bu bug'i fix et",                         "eng"),
    ("deploy yap production'a",                 "eng"),
    ("API refactor gerekiyor",                  "eng"),
    # Media
    ("youtube videosu hazirla",                 "media"),
    ("thumbnail tasarimi yap",                  "media"),
    ("SEO raporu cikar",                        "media"),
    ("script yaz video icin",                   "media"),
    # Academy
    ("egitim icerigi olustur",                  "academy"),
    ("pazar arastirmasi yap",                   "academy"),
    ("analiz raporu hazirla",                   "academy"),
    # Mystic / Strategy
    ("strateji plani hazirla",                  "mystic"),
    ("roadmap cikar Q3 icin",                   "mystic"),
    ("vizyon belirle",                          "mystic"),
    # Finance
    ("BTC fiyatini takip et",                   "fin"),
    ("butce raporu hazirla",                    "fin"),
    ("binance pozisyon kontrol et",             "fin"),
    # ARO: Sales, Marketing, Outreach
    ("satis kampanyasi planla",                 "aro"),
    ("musteri outreach yap",                    "aro"),
    ("marketing plani olustur",                 "aro"),
    ("lead listesi cikart",                     "aro"),
    ("teklif hazirla yeni musteri icin",        "aro"),
    # Telegram
    ("telegram'a bildirim gonder",              "telegram"),
    ("bot mesaj gonder",                        "telegram"),
    # Safe Fallback
    ("bilinmeyen rastgele gorev xyz123",        "general"),
    ("hava durumu nedir",                       "general"),
]


async def run_dry_run():
    mq = DummyMQ()
    router = RouterAgent(mq)

    print("=" * 65)
    print("   FULL AUTONOMOUS ORCHESTRATION DRY-RUN")
    print("   Mode: DummyMQ | No Docker | No RabbitMQ | No API")
    print("=" * 65)

    passed = 0
    failed = 0
    for desc, expected_agent in CASES:
        result = await router.route_task(desc, {})
        got_agent = result.get("agent", "?")
        task_id   = result.get("task_id", "?")
        status    = result.get("status", "?")
        ok = (got_agent == expected_agent
              and status == "dispatched"
              and len(task_id) == 36)
        if ok:
            passed += 1
            icon = "PASS"
        else:
            failed += 1
            icon = "FAIL"
        got_q = f"zeze_{got_agent}_queue"
        exp_q = f"zeze_{expected_agent}_queue"
        marker = "" if ok else f" !! expected={exp_q}"
        print(f"  [{icon}] '{desc[:42]}' -> {got_q}{marker}")

    print()
    print(f"  ROUTING RESULTS: {passed}/{passed + failed} PASSED, {failed} FAILED")
    print()

    # ── UUID CHECK ────────────────────────────────────────────────────
    all_uuids = [e[1] for e in mq.log]
    unique_uuids = len(set(all_uuids)) == len(all_uuids)
    print(f"  [{'PASS' if unique_uuids else 'FAIL'}] All task_ids are unique UUIDs: {unique_uuids}")

    # ── DLQ PATH TEST ─────────────────────────────────────────────────
    print()
    print("  DLQ FAILURE PATH TEST:")
    fail_mq = FailMQ()
    router2 = RouterAgent(fail_mq)
    result2 = await router2.route_task("kod yaz", {})
    dlq_ok = any(e[0] == "zom_dead_letter_queue" for e in fail_mq.log)
    status_ok = result2.get("status") == "error"
    print(f"  [{'PASS' if dlq_ok else 'FAIL'}] Publish failure -> DLQ published: {dlq_ok}")
    print(f"  [{'PASS' if status_ok else 'FAIL'}] Return status 'error' on failure: {status_ok}")

    print()
    print("=" * 65)
    all_ok = (failed == 0 and unique_uuids and dlq_ok and status_ok)
    if all_ok:
        print("  SONUC: FULL AUTONOMOUS DRY-RUN BASARILI")
    else:
        print("  SONUC: DRY-RUN KISMI BASARISIZ - yukarida FAIL satirlarini kontrol et")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(run_dry_run())
