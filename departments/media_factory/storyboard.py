"""
Storyboard — sahne-sahne çekim planı (video üretiminin omurgası, görsel tutarlılığın anahtarı).

Teknik (2026 araştırma): Senaryo → sahne sınırları → KEY BEAT'ler → her beat bir KARE.
Her kare: çekim tipi + kamera açısı + hareket + özne + ışık/mood + GLM-prompt + karakter tutarlılığı.
Karakter/mekan REFERANSLARI her karede tekrar edilir → kişiler/mekanlar shot'tan shot'a sabit kalır.

Çıktı GLM görüntü yönetmenini besler (rastgele değil PLANLI sahne).
"""
from __future__ import annotations
import re
import json
from typing import List, Dict, Optional

# Çekim dili (storyboard vokabüleri)
SHOT_TYPES = ["wide shot", "medium shot", "close-up", "extreme close-up",
              "over-the-shoulder", "POV", "establishing shot", "two-shot"]
CAMERA_ANGLES = ["eye-level", "low angle", "high angle", "bird's eye", "dutch tilt"]
MOVEMENTS = ["static", "slow push-in", "slow pull-out", "pan", "tracking", "handheld"]


def build_consistency_block(characters: List[Dict]) -> str:
    """Karakter/mekan tutarlılık çapası — her shot prompt'una eklenecek sabit tanım.
    characters: [{name, look}] — look: değişmez görünüm tanımı (kıyafet/saç/yaş)."""
    if not characters:
        return ""
    parts = [f"{c.get('name')}: {c.get('look','')}" for c in characters if c.get('name')]
    return "CONSISTENT CHARACTERS — " + "; ".join(parts)


async def generate_storyboard(ask_llm, premise: str, num_shots: int = 6,
                              characters: Optional[List[Dict]] = None, lang: str = "tr",
                              vertical: bool = True, style: str = "cinematic") -> Optional[Dict]:
    """Senaryo/premise'ten sahne-sahne storyboard üret. Her kare GLM-hazır görsel prompt içerir."""
    # 1. Karakter görünüm referansı yoksa LLM'den iste (tutarlılık için)
    if characters is None:
        cresp = await ask_llm(
            prompt=f"'{premise}' için ana karakterlerin DEĞİŞMEZ görünüm tanımları (kıyafet/saç/yaş/ten). "
                   f"SADECE JSON: {{\"characters\":[{{\"name\":\"\",\"look\":\"\"}}]}}",
            system_prompt="Sen karakter tasarımcısısın. Tutarlı, görsel-spesifik tanımlar verirsin.")
        try:
            characters = json.loads(re.search(r'\{.*\}', cresp, re.DOTALL).group(0)).get("characters", [])
        except Exception:
            characters = []

    consistency = build_consistency_block(characters)
    aspect = "vertical 9:16" if vertical else "horizontal 16:9"

    # 2. Sahne→beat→kare: her kare çekim-dili + GLM-prompt
    prompt = (
        f"'{premise}' için {num_shots} kareli STORYBOARD üret ({aspect}, {style}).\n"
        f"Senaryoyu beat'lere böl; her beat = bir kare. Her kare için:\n"
        f"- shot_type ({'/'.join(SHOT_TYPES[:6])}), camera_angle ({'/'.join(CAMERA_ANGLES)}), "
        f"movement ({'/'.join(MOVEMENTS)})\n"
        f"- beat (an/duygu), duration_sec, dialogue_or_vo ({lang})\n"
        f"- visual_prompt: GLM için İNGİLİZCE, spesifik (özne+aksiyon+açı+ışık+mood+{style}). "
        f"Tutarlılık için karakter görünümünü prompt'a göm.\n"
        f"KARAKTER REFERANSI (her görselde aynı kalmalı): {consistency}\n"
        f'SADECE JSON: {{"shots":[{{"shot_num":1,"beat":"","shot_type":"","camera_angle":"",'
        f'"movement":"","duration_sec":5,"dialogue_or_vo":"","visual_prompt":""}}]}}'
    )
    resp = await ask_llm(prompt, system_prompt="Sen sinematik storyboard sanatçısısın. Çekim dili (açı/tip/hareket) ve görsel-spesifik prompt ustası.")
    try:
        data = json.loads(re.search(r'\{.*\}', resp, re.DOTALL).group(0))
        shots = data.get("shots", [])
    except Exception:
        return None
    if not shots:
        return None
    # Tutarlılık çapasını her görsel prompt'una garanti ekle
    for s in shots:
        vp = s.get("visual_prompt", "")
        if consistency and consistency not in vp:
            s["visual_prompt"] = f"{vp}. {consistency}. {style}, {aspect}"
    return {"premise": premise, "characters": characters, "consistency": consistency,
            "aspect": aspect, "shots": shots,
            "visual_prompts": [s.get("visual_prompt", "") for s in shots]}
