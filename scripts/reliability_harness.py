"""
Reliability Harness — gerçek AI holding için güvenilirlik ölçümü.

pass@1 (tek koşu) güvenilirliği ABARTIR. Gerçek görevler binlerce kez çağrılır;
soru "tutarlı başarı oranı nedir?". Bu harness her departmanı N kez çalıştırır ve
üretim-gerçeği metriklerini raporlar:
  - başarı oranı (success rate)  — pass^k mantığı
  - deliverable oranı             — somut artefakt üretti mi
  - coverage_miss oranı           — kör nokta (generic'e düşme)
  - p50 / p95 gecikme             — kuyruk değil, gerçek süre dağılımı

Kullanım:
  python scripts/reliability_harness.py            # tüm dept, 5 koşu
  python scripts/reliability_harness.py --runs 10 --depts zeze_ops,zeze_sec
"""
import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# .env yükle (ZOM_PRIMARY_PROVIDER vb. routing ayarları için)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"), override=True)
except Exception:
    pass

# (department_id, AgentClass module path, class name, örnek görev)
CASES = [
    ("zeze_ops",        "departments.zeze_ops.agent",        "ZezeOpsAgent",        "Sistem operasyon denetimi ve optimizasyon"),
    ("zeze_compliance", "departments.zeze_compliance.agent", "ZezeComplianceAgent", "KVKK uyumluluk denetimi"),
    ("zeze_game",       "departments.zeze_game.agent",       "ZezeGameAgent",       "Mobil puzzle oyunu mekaniği"),
    ("zeze_business",   "departments.zeze_business.agent",   "ZezeBusinessAgent",   "SaaS pazarı TAM/SAM analizi"),
    ("zeze_trend",      "departments.zeze_trend.agent",      "ZezeTrendAgent",      "AI ajan pazarı trend analizi"),
    ("zeze_production", "departments.zeze_production.agent",  "ZezeProductionAgent", "Video içerik üretim planı"),
    ("zeze_comms",      "departments.zeze_comms.agent",      "ZezeCommsAgent",      "Ürün lansmanı basın bülteni"),
    ("zeze_dev",        "departments.zeze_dev.agent",        "ZezeDevAgent",        "is_even(n) fonksiyonu yaz ve pytest ekle"),
    ("app_factory",     "departments.app_factory.agent",     "AppFactoryAgent",     "FastAPI todo uygulaması scaffold oluştur"),
    ("crypto_trading",  "departments.crypto_trading.agent",  "CryptoTradingAgent",  "BTC için kısa piyasa analizi yap"),
    ("media_factory",   "departments.media_factory.agent",   "MediaFactoryAgent",   "Tanıtım videosu konsepti hazırla"),
    ("zeze_academy",    "departments.zeze_academy.agent",    "ZezeAcademyAgent",    "Python başlangıç eğitim müfredatı"),
    ("zeze_aro",        "departments.zeze_aro.agent",        "ZezeAroAgent",        "Büyüme metrikleri analizi"),
    ("zeze_sec",        "departments.zeze_sec.agent",        "ZezeSecAgent",        "Kod güvenlik denetimi yap"),
    ("zeze_design",     "departments.zeze_design.agent",     "ZezeDesignAgent",     "Dashboard için renk paleti ve layout tasarla"),
    ("zeze_rnd",        "departments.zeze_rnd.agent",        "ZezeRndAgent",        "Yeni TTS teknolojilerini tara ve test et"),
    ("zeze_betting",    "departments.zeze_betting.agent",    "ZezeBettingAgent",    "Maç tahmin istatistik analizi"),
]


def _percentile(values, pct):
    if not values:
        return None
    s = sorted(values)
    k = int(round((pct / 100.0) * (len(s) - 1)))
    return round(s[k], 1)


async def _run_case(dept, module_path, cls_name, desc, runs, timeout):
    m = __import__(module_path, fromlist=[cls_name])
    AgentCls = getattr(m, cls_name)
    durations, ok, deliv, cov_miss, errors = [], 0, 0, 0, 0
    import uuid as _uuid
    for i in range(runs):
        agent = AgentCls(workspace_root=".")
        t0 = time.time()
        # Benzersiz task_id + açıklama varyasyonu: anti-loop/cache yanlış-pozitiflerini önle
        nonce = _uuid.uuid4().hex[:6]
        try:
            r = await asyncio.wait_for(
                agent.execute_task({"task_id": f"rel-{dept}-{nonce}", "description": f"{desc} (vaka #{i+1})"}),
                timeout=timeout,
            )
            durations.append(time.time() - t0)
            if r.get("success"):
                ok += 1
            if r.get("deliverable"):
                deliv += 1
            if r.get("coverage_miss"):
                cov_miss += 1
        except Exception:
            errors += 1
            durations.append(time.time() - t0)
    return {
        "department": dept,
        "runs": runs,
        "success_rate": round(ok / runs * 100, 1),
        "deliverable_rate": round(deliv / runs * 100, 1),
        "coverage_miss_rate": round(cov_miss / runs * 100, 1),
        "error_count": errors,
        "p50_s": _percentile(durations, 50),
        "p95_s": _percentile(durations, 95),
    }


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--timeout", type=float, default=120.0)
    ap.add_argument("--depts", type=str, default="")
    args = ap.parse_args()

    cases = CASES
    if args.depts:
        wanted = {d.strip() for d in args.depts.split(",")}
        cases = [c for c in CASES if c[0] in wanted]

    print(f"[Reliability Harness] {len(cases)} departman × {args.runs} koşu, timeout={args.timeout}s\n")
    results = []
    for dept, mod, cls, desc in cases:
        print(f"  çalışıyor: {dept} ...", flush=True)
        results.append(await _run_case(dept, mod, cls, desc, args.runs, args.timeout))

    print("\n===== GÜVENİLİRLİK RAPORU =====")
    print(f"{'DEPT':<18}{'BAŞARI%':<9}{'DELIV%':<8}{'KÖR%':<7}{'HATA':<6}{'p50s':<7}{'p95s'}")
    for r in results:
        print(f"{r['department']:<18}{r['success_rate']:<9}{r['deliverable_rate']:<8}"
              f"{r['coverage_miss_rate']:<7}{r['error_count']:<6}{str(r['p50_s']):<7}{r['p95_s']}")

    avg_success = round(sum(r["success_rate"] for r in results) / len(results), 1) if results else 0
    print(f"\nORTALAMA BAŞARI ORANI: {avg_success}%")

    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "reliability_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "runs": args.runs, "results": results,
                   "avg_success_rate": avg_success}, f, indent=2, ensure_ascii=False)
    print(f"Rapor: {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
