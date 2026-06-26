"""
Virality Engine — script viral-potansiyel skorlayıcı (Spikes-tarzı ölçüm, unicorn-seviye).

media_factory script ÜRETİYOR ama kalitesini ÖLÇMÜYORDU. Bu motor üretilen script'i
kanıtlı viral mekaniklere göre 0-100 skorlar + somut düzeltme verir. Saf, deterministik,
test edilebilir (LLM/ağ yok). Düşük skor → revizyon gate.
"""
from __future__ import annotations
import re
from typing import Dict, List

# Hook sinyali kalıpları (ilk satır/3sn'de aranır)
_HOOK_PATTERNS = [
    r"\?", r"\bsakın\b", r"\bbırak\b", r"\bçoğu\b", r"\byanlış\b", r"\bkimse\b", r"\bsır\b",
    r"\bnasıl\b", r"\bneden\b", r"\bbunu\b", r"\bhata\b", r"\bsandığın\b", r"\bgerçek\b",
    r"\b\d+\s+(şey|adım|sır|hata|yol|neden)\b", r"\bdur\b", r"\bdikkat\b", r"\bhemen\b",
]
_CTA_PATTERNS = [r"takip et", r"yorum", r"kaydet", r"paylaş", r"abone", r"link", r"beğen",
                 r"profil", r"dm at", r"tıkla", r"deneyin", r"yaz "]
_STRUCTURE = {
    "hook": _HOOK_PATTERNS,
    "problem": [r"\bproblem\b", r"\bsorun\b", r"\bzorlan", r"\bacı\b", r"\bistiyorsan\b", r"\bnefret\b", r"\btakılıyor"],
    "solution": [r"\bçözüm\b", r"\bişte\b", r"\byap\b", r"\byöntem\b", r"\badım\b", r"\bböyle\b", r"\bşöyle\b", r"\bsırrı\b"],
    "cta": _CTA_PATTERNS,
}


def _has_any(text: str, patterns: List[str]) -> bool:
    low = text.lower()
    return any(re.search(p, low) for p in patterns)


def score_script(script: str, target_seconds: int = 30, platform: str = "shorts") -> Dict:
    """Script'i viral mekaniklere göre 0-100 skorla + somut düzeltme. ~150 kelime/dk konuşma."""
    text = (script or "").strip()
    if not text:
        return {"score": 0, "grade": "F", "fixes": ["boş script"], "checks": {}}
    lines = [l for l in text.splitlines() if l.strip()]
    words = re.findall(r"\w+", text)
    wc = len(words)
    first_chunk = " ".join(lines[:2]) if lines else text[:120]

    checks = {}
    fixes = []
    score = 0.0

    # 1. HOOK ilk 3 saniyede (en kritik — 30 puan)
    hook_ok = _has_any(first_chunk, _HOOK_PATTERNS)
    checks["hook_first"] = hook_ok
    if hook_ok:
        score += 30
    else:
        fixes.append("İlk 1-2 satıra net hook ekle (soru/kontrarian/merak boşluğu)")

    # 2. HPSC yapı (Hook→Problem→Çözüm→CTA — 30 puan, her biri 7.5)
    for part, pats in _STRUCTURE.items():
        ok = _has_any(text, pats)
        checks[f"struct_{part}"] = ok
        if ok:
            score += 7.5
        else:
            fixes.append(f"Yapı eksik: '{part}' bölümü yok (Hook→Problem→Çözüm→CTA)")

    # 3. Uzunluk/pacing fit (~150 kelime/dk → target_seconds*2.5 kelime; 20 puan)
    ideal = target_seconds * 2.5
    ratio = wc / ideal if ideal else 0
    if 0.6 <= ratio <= 1.4:
        score += 20
        checks["length_fit"] = True
    else:
        checks["length_fit"] = False
        fixes.append(f"Uzunluk {wc} kelime; {target_seconds}sn için ~{int(ideal)} ideal "
                     f"({'çok uzun, kes' if ratio > 1.4 else 'çok kısa, derinleştir'})")

    # 4. Pattern interrupt / sahne dinamiği (10 puan)
    interrupts = len(re.findall(r"\[(?:kesme|geçiş|sahne|cut|b-roll|zoom|görsel)\]", text.lower())) \
        + text.count("→") + len(re.findall(r"\bama\b|\bfakat\b|\bbir anda\b|\bsonra\b", text.lower()))
    checks["pattern_interrupt"] = interrupts >= 2
    if interrupts >= 2:
        score += 10
    else:
        fixes.append("Pattern interrupt ekle (sahne/ton değişimi, 'ama...', görsel kesme)")

    # 5. CTA netliği (10 puan) — yapıdan ayrı, açık eylem
    checks["cta_clear"] = checks.get("struct_cta", False)
    if checks["cta_clear"]:
        score += 10

    score = round(min(100, score))
    grade = "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D" if score >= 35 else "F"
    return {"score": score, "grade": grade, "word_count": wc,
            "viral_ready": score >= 65, "checks": checks, "fixes": fixes}
