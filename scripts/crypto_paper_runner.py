"""
Crypto Paper-Proof Runner — kanıt biriktirme modu.

run_alpha_cycle'ı çalıştırır, her döngüyü loglar, P3 işlem defterinden gerçek
performans özeti üretir. Periyodik çalıştır (cron/zamanlayıcı) → 2-4 hafta gerçek
veriyle win-rate/getiri/maxDD biriksin. Kanıt olmadan canlıya geçiş YOK.

Kullanım:
    python scripts/crypto_paper_runner.py            # bir döngü + özet
    python scripts/crypto_paper_runner.py --report   # sadece performans özeti
"""
import asyncio
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "departments", "crypto_trading", "paper_state")
CYCLE_LOG = os.path.join(LOG_DIR, "alpha_cycle_log.jsonl")


async def run_once(score_threshold: int = 60):
    from departments.crypto_trading.agent import CryptoTradingAgent
    agent = CryptoTradingAgent(workspace_root=os.path.dirname(LOG_DIR.split("departments")[0]))
    cycle = await agent.run_alpha_cycle(top_n=8, score_threshold=score_threshold)
    cycle["ts"] = datetime.now(timezone.utc).isoformat()
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(CYCLE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(cycle, ensure_ascii=False) + "\n")
    return agent, cycle


async def performance_report(agent=None):
    if agent is None:
        from departments.crypto_trading.agent import CryptoTradingAgent
        agent = CryptoTradingAgent(workspace_root=os.path.dirname(LOG_DIR.split("departments")[0]))
    perf = await agent.get_live_performance()
    # döngü logu istatistiği
    cycles, opened = 0, 0
    if os.path.exists(CYCLE_LOG):
        with open(CYCLE_LOG, encoding="utf-8") as f:
            for line in f:
                try:
                    c = json.loads(line)
                    cycles += 1
                    opened += c.get("positions_opened", 0)
                except json.JSONDecodeError:
                    pass
    return {"cycles_run": cycles, "positions_opened_total": opened,
            "closed_trades": perf["trades"], "live_win_rate_pct": perf["win_rate_pct"]}


def _w(s):
    sys.stdout.buffer.write((str(s) + "\n").encode("utf-8", "replace"))


async def main():
    report_only = "--report" in sys.argv
    agent = None
    if not report_only:
        agent, cycle = await run_once()
        _w(f"[DÖNGÜ {cycle['ts'][:16]}] aktif_saat={cycle['is_active_hour']} "
           f"fırsat={cycle['opportunities_found']} açılan={cycle['positions_opened']}")
        for ac in cycle["actions"][:5]:
            _w(f"   {ac['symbol']:12s} {ac['decision']}")
    rep = await performance_report(agent)
    _w("=== PAPER KANIT ÖZETİ ===")
    _w(f"  Toplam döngü: {rep['cycles_run']} | açılan pozisyon: {rep['positions_opened_total']}")
    _w(f"  Kapanan işlem: {rep['closed_trades']} | CANLI WIN-RATE: %{rep['live_win_rate_pct']}")
    if rep["closed_trades"] < 20:
        _w(f"  ⏳ Kanıt yetersiz ({rep['closed_trades']}/20 işlem). Canlıya geçiş için biriktirmeye devam.")
    else:
        _w(f"  ✅ Yeterli örneklem. Win-rate >%55 ise küçük canlı sermaye değerlendirilebilir.")


if __name__ == "__main__":
    asyncio.run(main())
