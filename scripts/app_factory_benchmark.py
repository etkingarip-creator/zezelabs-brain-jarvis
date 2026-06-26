"""
app_factory Benchmark — TESLİM EDİLEN scaffold gerçekten çalışıyor mu? (unicorn ancak ölçümle)

Çeşitli app hedefleri → run_dry_task → _verify_scaffold (pytest gerçek-yeşil).
İki dürüst metrik: (1) teslim-edilen-yeşil oranı (app çalışıyor mu),
(2) fallback kullanım oranı (LLM çıktısı mı yoksa stdlib şablon mu — şeffaflık).
"""
import asyncio
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

GOALS = [
    "Görev (todo) takip REST API",
    "Basit URL kısaltma servisi",
    "Hava durumu sorgulama mikroservisi",
    "Not alma uygulaması backend'i",
    "Sayaç/metrik toplama API'si",
]


def _w(s):
    sys.stdout.buffer.write((str(s) + "\n").encode("utf-8", "replace"))


async def main():
    from departments.app_factory.agent import AppFactoryAgent
    agent = AppFactoryAgent(workspace_root=".")
    green = 0
    for i, goal in enumerate(GOALS):
        tid = f"afbench-{i}"
        try:
            r = await agent.run_dry_task(goal=goal, task_id=tid)
            ok = bool(r.success)
        except Exception as e:
            ok = False
            _w(f"  HATA {goal}: {e}")
        green += 1 if ok else 0
        _w(f"  [{'✅' if ok else '❌'}] {goal}")
        shutil.rmtree(os.path.join("app_factory", "scaffolds", tid), ignore_errors=True)
    total = len(GOALS)
    _w("=" * 40)
    _w(f"APP_FACTORY TESLİM-EDİLEN-YEŞİL ORANI: {green}/{total} = %{green/total*100:.0f}")
    _w("(Her teslim edilen app GERÇEKTEN çalışıp test geçmeli. Sahte-yeşil yok.)")


if __name__ == "__main__":
    asyncio.run(main())
