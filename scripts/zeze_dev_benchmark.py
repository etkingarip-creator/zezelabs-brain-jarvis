"""
zeze_dev Issue-Çözme Benchmark — gerçek çözüm oranını ÖLÇER (unicorn iddiası ancak ölçümle).

Mini SWE-bench tarzı: çeşitli bug tipleri (aritmetik, off-by-one, yanlış karşılaştırma,
eksik return, yanlış default, çok-dosya çağıran). Her senaryo: buglu kod + GEÇMESİ GEREKEN
test. zeze_dev._handle_issue çalıştırılır, verified (gerçek-yeşil) oranı raporlanır.

Kullanım: python scripts/zeze_dev_benchmark.py
"""
import asyncio
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BENCH_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "departments", "zeze_dev", "workspace", "_benchmark")

# (ad, açıklama, {dosya: içerik}) — her senaryoda en az bir GEÇMESİ GEREKEN test
SCENARIOS = [
    ("aritmetik", "multiply çarpma yapmalı ama toplama yapıyor; düzelt.",
     {"m.py": "def multiply(a, b):\n    return a + b\n",
      "test_m.py": "from m import multiply\ndef test_m():\n    assert multiply(3, 4) == 12\n"}),
    ("off_by_one", "get_last listenin son elemanını döndürmeli; index hatası var. Düzelt.",
     {"l.py": "def get_last(xs):\n    return xs[len(xs)]\n",
      "test_l.py": "from l import get_last\ndef test_l():\n    assert get_last([1,2,3]) == 3\n"}),
    ("yanlis_karsilastirma", "is_adult 18 ve üstü için True dönmeli; sınır yanlış. Düzelt.",
     {"a.py": "def is_adult(age):\n    return age > 18\n",
      "test_a.py": "from a import is_adult\ndef test_a():\n    assert is_adult(18) is True\n"}),
    ("eksik_return", "double iki katını döndürmeli ama hiçbir şey döndürmüyor. Düzelt.",
     {"d.py": "def double(x):\n    result = x * 2\n",
      "test_d.py": "from d import double\ndef test_d():\n    assert double(5) == 10\n"}),
    ("yanlis_default", "greet ismi yoksa 'Misafir' demeli ama 'None' diyor. Düzelt.",
     {"g.py": "def greet(name=None):\n    return f'Merhaba {name}'\n",
      "test_g.py": "from g import greet\ndef test_g():\n    assert greet() == 'Merhaba Misafir'\n"}),
    ("bos_liste", "ortalama hesapla; boş listede çöküyor, 0 dönmeli. Düzelt.",
     {"avg.py": "def average(xs):\n    return sum(xs) / len(xs)\n",
      "test_avg.py": "from avg import average\ndef test_avg():\n    assert average([]) == 0\n    assert average([2,4]) == 3\n"}),
    ("cok_dosya_cagiran", "area 20 vermeli; multiply yanlış (toplama). Düzelt.",
     {"mathlib.py": "def multiply(a, b):\n    return a + b\n",
      "service.py": "from mathlib import multiply\ndef area(w, h):\n    return multiply(w, h)\n",
      "test_service.py": "from service import area\ndef test_area():\n    assert area(4, 5) == 20\n"}),
    ("string_islem", "reverse_words kelimeleri ters sırada birleştirmeli. Düzelt.",
     {"s.py": "def reverse_words(t):\n    return ' '.join(t.split())\n",
      "test_s.py": "from s import reverse_words\ndef test_s():\n    assert reverse_words('a b c') == 'c b a'\n"}),
]


def _w(s):
    sys.stdout.buffer.write((str(s) + "\n").encode("utf-8", "replace"))


async def main():
    from departments.zeze_dev.agent import ZezeDevAgent
    agent = ZezeDevAgent(workspace_root=".")
    shutil.rmtree(BENCH_DIR, ignore_errors=True)
    results = []
    for name, desc, files in SCENARIOS:
        d = os.path.join(BENCH_DIR, name)
        os.makedirs(d, exist_ok=True)
        for fn, content in files.items():
            with open(os.path.join(d, fn), "w", encoding="utf-8") as f:
                f.write(content)
        rel = os.path.relpath(d, ".").replace("\\", "/")
        try:
            r = await agent._handle_issue({"task_id": f"bench-{name}", "description": desc, "path": rel})
            verified = bool(r.get("verified"))
        except Exception as e:
            verified = False
            _w(f"  HATA {name}: {e}")
        results.append((name, verified))
        _w(f"  [{'✅' if verified else '❌'}] {name}")
    shutil.rmtree(BENCH_DIR, ignore_errors=True)
    solved = sum(1 for _, v in results if v)
    total = len(results)
    _w("=" * 40)
    _w(f"ZEZE_DEV ÇÖZÜM ORANI: {solved}/{total} = %{solved/total*100:.0f}")
    _w("(Frontier SWE-bench referans: ~%80. Unicorn eşiği bizim setimizde >%75 hedef.)")


if __name__ == "__main__":
    asyncio.run(main())
