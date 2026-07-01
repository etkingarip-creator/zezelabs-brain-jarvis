"""
Channel Setup — bir niş için tam kanal kurulum paketi (ad, handle, about, SEO, playlist,
yükleme varsayılanları, banner/avatar promptları, ilk video fikirleri).

Kanal video kadar önemli: keşfedilebilirlik + marka güveni + affiliate hunisi buradan başlar.
Ollama/LLM üretir; kod affiliate/yapı iskeletini zorlar.
"""
from __future__ import annotations
import re
import json
from typing import Dict, List


async def generate_channel_package(ask_llm, niche: str, audience: str,
                                   affiliates: List[Dict], lang: str = "en") -> Dict:
    """Niş → tam kanal kimliği + SEO + yükleme varsayılanları paketi."""
    aff = ", ".join(a["name"] for a in affiliates) if affiliates else "relevant affiliate programs"
    prompt = (
        f"Design a complete YouTube channel setup for a faceless {niche} channel.\n"
        f"AUDIENCE: {audience}. Language: {lang}. Monetization: affiliate-first ({aff}) + AdSense.\n"
        f"Give: 3 brandable channel name ideas + a handle; a 1-line tagline; a full channel ABOUT "
        f"description (what viewers get, upload cadence, keywords woven naturally, 1-line affiliate "
        f"disclosure); 15 SEO keywords; 12 channel tags; 5 playlist names; a default video-description "
        f"TEMPLATE (affiliate links top placeholder, chapters, subscribe CTA, disclosure); 5 hashtags; "
        f"a posting schedule; an Imagen prompt for the banner and one for the logo/avatar; 10 first video ideas.\n"
        f'ONLY JSON: {{"name_options":["3"],"handle":"@","tagline":"","about":"","seo_keywords":["15"],'
        f'"channel_tags":["12"],"playlists":["5"],"description_template":"","hashtags":["5"],'
        f'"posting_schedule":"","banner_prompt":"","avatar_prompt":"","first_10_ideas":["10"]}}'
    )
    resp = await ask_llm(prompt=prompt, system_prompt="You are a YouTube channel strategist + brand designer. Output ONLY valid JSON.")
    try:
        m = re.search(r"```(?:json)?\s*(.*?)```", resp, re.DOTALL)
        s = m.group(1) if m else resp
        b = re.search(r"\{.*\}", s, re.DOTALL)
        pkg = json.loads(b.group(0) if b else s)
    except Exception:
        pkg = {}
    # güvenli iskelet (LLM düşükse bile paket eksiksiz dönsün)
    base = niche.split()[0].title()
    pkg.setdefault("name_options", [f"{base} Uncovered", f"Wander {base}", f"{base} in 60s"])
    pkg.setdefault("handle", "@" + base.lower() + "shorts")
    pkg.setdefault("tagline", f"Your {niche} in 60 seconds.")
    pkg.setdefault("about", f"Fast, beautiful {niche} shorts for {audience}. New videos weekly.")
    pkg.setdefault("seo_keywords", [niche, f"{niche} shorts", f"best {niche}", f"{niche} 2026"])
    pkg.setdefault("channel_tags", pkg["seo_keywords"])
    pkg.setdefault("playlists", [f"Top {base} Spots", f"{base} Shorts", "Hidden Gems"])
    pkg.setdefault("description_template", "👉 Links & full guide below\n\n{affiliate_links}\n\n⏱️ Chapters\n\n🔔 Subscribe\n\nℹ️ Some links are affiliate links.")
    pkg.setdefault("hashtags", [f"#{base}", "#travel", "#shorts"])
    pkg.setdefault("posting_schedule", "3-5 shorts/week, 1 long-form/week")
    pkg.setdefault("banner_prompt", f"cinematic {niche} banner, bold, high contrast, minimal text space")
    pkg.setdefault("avatar_prompt", f"clean modern {niche} logo, bold icon, high contrast")
    pkg.setdefault("first_10_ideas", [])
    pkg["affiliates"] = affiliates
    return pkg


def render_markdown(pkg: Dict, niche: str) -> str:
    """Paketi okunur markdown dokümanına çevir (kullanıcı YouTube Studio'ya kopyalar)."""
    L = [f"# {niche.title()} Kanalı — Kurulum Paketi\n"]
    L.append("## Kanal Adı Seçenekleri\n" + "\n".join(f"- {n}" for n in pkg.get("name_options", [])))
    L.append(f"\n**Handle:** {pkg.get('handle','')}  \n**Tagline:** {pkg.get('tagline','')}")
    L.append("\n## Hakkında (About)\n" + str(pkg.get("about", "")))
    L.append("\n## SEO Anahtar Kelimeler\n" + ", ".join(pkg.get("seo_keywords", [])))
    L.append("\n## Kanal Etiketleri\n" + ", ".join(pkg.get("channel_tags", [])))
    L.append("\n## Playlistler\n" + "\n".join(f"- {p}" for p in pkg.get("playlists", [])))
    L.append("\n## Varsayılan Video Açıklama Şablonu\n```\n" + str(pkg.get("description_template", "")) + "\n```")
    L.append("\n## Hashtagler\n" + " ".join(pkg.get("hashtags", [])))
    L.append("\n## Yükleme Takvimi\n" + str(pkg.get("posting_schedule", "")))
    L.append("\n## Banner Promptu (Imagen)\n" + str(pkg.get("banner_prompt", "")))
    L.append("\n## Avatar/Logo Promptu (Imagen)\n" + str(pkg.get("avatar_prompt", "")))
    ideas = pkg.get("first_10_ideas", [])
    if ideas:
        L.append("\n## İlk 10 Video Fikri\n" + "\n".join(f"{i+1}. {x}" for i, x in enumerate(ideas)))
    affs = pkg.get("affiliates", [])
    if affs:
        L.append("\n## Affiliate Programları (kendi ID'lerinle doldur)\n" +
                 "\n".join(f"- {a['name']}: {a.get('url') or '<affiliate-link>'}" for a in affs))
    return "\n".join(L)
