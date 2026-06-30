"""
SEO + Affiliate Metadata Optimizer — başlık/etiket/açıklama/bölüm (video kadar önemli).

Affiliate geliri açıklama+başlık+SEO'dan büyük ölçüde gelir. Bu modül:
- Başlık: CTR + anahtar-kelime (öne-yüklü keyword + sonuç/merak).
- Etiketler: araştırılmış + affiliate-ilgili.
- Açıklama: affiliate-FIRST (linkler üstte) + bölümler (timestamps) + SEO keyword bloğu.
- Hashtag + pinned yorum.

LLM içeriği üretir; KOD affiliate yapısını (sıra, bölüm formatı) zorlar.
"""
from __future__ import annotations
import re
import json
from typing import List, Dict, Optional

from departments.media_factory import monetization_engine as money


async def generate_seo_fields(ask_llm, topic: str, tested_tools: List[str],
                              avatar: str = "AI entrepreneur") -> Dict:
    """LLM ile başlık adayları, anahtar kelimeler, etiketler, hook ve bölüm taslağı üret."""
    tools = ", ".join(tested_tools) if tested_tools else "AI tools"
    prompt = (
        f"You are a YouTube SEO + CTR expert for a faceless channel.\n"
        f"AUDIENCE: {avatar}. FORMAT: we ACTUALLY test an AI workflow and report real results.\n"
        f"TOPIC: {topic}. TOOLS TESTED: {tools}.\n"
        f"Produce SEO+affiliate-optimized metadata. Title: result/curiosity + front-loaded keyword, <70 chars.\n"
        f"Tags: 15 search-relevant + affiliate-relevant. Keywords: primary + 5 secondary.\n"
        f"Chapters: 5-7 (timestamp 0:00 style placeholders ok) matching tested-workflow structure.\n"
        f'ONLY JSON: {{"title":"","alt_titles":["2 more"],"primary_keyword":"","secondary_keywords":["..."],'
        f'"tags":["..."],"hook":"","one_takeaway":"","chapters":[{{"t":"0:00","label":""}}],"hashtags":["3-5"]}}'
    )
    resp = await ask_llm(prompt=prompt, system_prompt="YouTube SEO strategist. Output ONLY valid compact JSON.")
    try:
        m = re.search(r"```(?:json)?\s*(.*?)```", resp, re.DOTALL)
        s = m.group(1) if m else resp
        b = re.search(r"\{.*\}", s, re.DOTALL)
        return json.loads(b.group(0) if b else s)
    except Exception:
        return {"title": topic, "alt_titles": [], "primary_keyword": topic,
                "secondary_keywords": [], "tags": [], "hook": topic, "one_takeaway": "",
                "chapters": [], "hashtags": ["#AI", "#AItools"]}


def build_chapters_block(chapters: List[Dict]) -> str:
    """YouTube bölüm bloğu (ilk satır 0:00 olmalı → otomatik bölümler aktifleşir)."""
    if not chapters:
        return ""
    lines = ["⏱️ BÖLÜMLER / CHAPTERS"]
    has_zero = any((c.get("t", "").strip() in ("0:00", "00:00")) for c in chapters)
    if not has_zero:
        lines.append("0:00 Intro")
    for c in chapters:
        lines.append(f"{c.get('t','0:00')} {c.get('label','')}")
    return "\n".join(lines)


def build_full_description(seo: Dict, affiliate_tools: List[Dict], topic: str,
                           setup_guide_url: str = "", brand: str = "zezelabs") -> str:
    """Affiliate-FIRST açıklama + bölümler + SEO keyword bloğu (hepsi optimize)."""
    # 1. Affiliate-first çekirdek (mevcut motor)
    core = money.build_description(topic, affiliate_tools, setup_guide_url, brand)
    parts = [core, ""]
    # 2. Bölümler (retention + SEO)
    ch = build_chapters_block(seo.get("chapters", []))
    if ch:
        parts.append(ch); parts.append("")
    # 3. Tek-çıkarım (değer netliği)
    if seo.get("one_takeaway"):
        parts.append(f"✅ Bu videoda öğreneceğin: {seo['one_takeaway']}"); parts.append("")
    # 4. SEO keyword bloğu (doğal cümle + hashtag)
    kws = [seo.get("primary_keyword", "")] + (seo.get("secondary_keywords") or [])
    kws = [k for k in kws if k]
    if kws:
        parts.append("🔎 " + ", ".join(kws[:8]))
    tags = seo.get("hashtags") or []
    if tags:
        parts.append(" ".join(t if t.startswith("#") else "#" + t for t in tags[:5]))
    return "\n".join(parts).strip()


async def build_metadata_package(ask_llm, topic: str, tested_tools: List[str],
                                 affiliate_tools: List[Dict], avatar: str = "AI entrepreneur",
                                 setup_guide_url: str = "", brand: str = "zezelabs") -> Dict:
    """Tam optimize paket: başlık + etiketler + bölümlü affiliate açıklama + pinned yorum."""
    seo = await generate_seo_fields(ask_llm, topic, tested_tools, avatar)
    desc = build_full_description(seo, affiliate_tools, topic, setup_guide_url, brand)
    primary = (affiliate_tools[0] if affiliate_tools else {})
    pinned = money.build_pinned_comment(primary.get("name", tested_tools[0] if tested_tools else topic),
                                        primary.get("url", ""), brand)
    return {
        "title": seo.get("title", topic),
        "alt_titles": seo.get("alt_titles", []),  # A/B testi için
        "description": desc,
        "tags": seo.get("tags", []),
        "hashtags": seo.get("hashtags", []),
        "chapters": seo.get("chapters", []),
        "primary_keyword": seo.get("primary_keyword", ""),
        "hook": seo.get("hook", ""),
        "pinned_comment": pinned,
    }
