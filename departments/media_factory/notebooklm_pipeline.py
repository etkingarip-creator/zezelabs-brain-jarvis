"""
NotebookLM Pipeline — en doğal ses (Gemini), ücretsiz (Gemini Pro kotası), EN podcast içeriği.

Mimari: tüketici NotebookLM'in ücretsiz API'si yok → TEK manuel adım NotebookLM'de ses üretmek.
Departman gerisini otomatik yapar:
  1. prepare_source: konu → NotebookLM'e yapıştırılacak KAYNAK metni + odak-promtu + başlık (otomatik)
  2. (kullanıcı NotebookLM'de EN Audio Overview üretir → mp3 indirir → inbox klasörüne koyar)
  3. assemble_from_audio: mp3 → storyboard+GLM görsel + Editor montaj + altyazı → finished video
"""
from __future__ import annotations
import os
import re
import json
import subprocess
from typing import Dict, Optional, List


async def prepare_source(ask_llm, topic: str, lang: str = "en") -> Dict:
    """NotebookLM'e verilecek KAYNAK paketi: zengin briefing metni + odak promtu + başlık.
    NotebookLM bu kaynağı 2 sunucuyla tartışır → doğal podcast."""
    prompt = (
        f"Create a rich English SOURCE DOCUMENT for a NotebookLM Audio Overview about: {topic}.\n"
        f"This document is what 2 AI hosts will DISCUSS. Make it informative, specific, with "
        f"surprising facts, a clear angle, 600-900 words, structured (intro, 3-4 key points, takeaway).\n"
        f"Also give a focus_prompt (1 sentence telling NotebookLM what angle/tone to take) and a "
        f"catchy English youtube_title.\n"
        f'ONLY JSON: {{"source_document":"...","focus_prompt":"...","youtube_title":"..."}}'
    )
    resp = await ask_llm(prompt=prompt, system_prompt="You are a podcast research writer. Specific, factual, engaging EN source material.")
    try:
        return json.loads(re.search(r'\{.*\}', resp, re.DOTALL).group(0))
    except Exception:
        return {"source_document": topic, "focus_prompt": f"Discuss {topic} engagingly", "youtube_title": topic}


def _ffprobe_duration(path: str) -> float:
    try:
        r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                            "-of", "default=noprint_wrappers=1:nokey=1", path],
                           capture_output=True, text=True, timeout=30)
        return float(r.stdout.strip())
    except Exception:
        return 0.0


async def assemble_from_audio(audio_path: str, topic: str, output_path: str,
                              video_pipeline=None, crew=None, ask_llm=None,
                              vertical: bool = False, scene_count: int = 4) -> Optional[Dict]:
    """NotebookLM ses dosyasını (mp3) bitmiş videoya çevir: storyboard→GLM görsel + Editor montaj.
    Ses NotebookLM'den (doğal); görsel+montaj departmandan."""
    if not (audio_path and os.path.exists(audio_path)):
        return {"success": False, "error": "ses dosyası yok: " + str(audio_path)}
    dur = _ffprobe_duration(audio_path)
    if dur <= 0:
        return {"success": False, "error": "ses süresi okunamadı"}

    # 1. Storyboard → görsel prompt'ları (konuya uygun, planlı)
    visuals = None
    if crew and video_pipeline:
        sb = None
        if ask_llm:
            sb = await crew.storyboard.draft(ask_llm, topic, num_shots=scene_count,
                                             vertical=vertical, style="clean modern explainer cinematic")
        prompts = (sb.get("visual_prompts") if sb else None) or [
            f"{topic}, clean modern explainer b-roll, cinematic" for _ in range(scene_count)]
        rep = os.path.dirname(output_path)
        visuals = await crew.dop.shoot(prompts[:scene_count], rep, vertical=vertical)

    if not visuals:  # görsel yoksa sakin gradyan zemin
        wh = "1080x1920" if vertical else "1920x1080"
        rep = os.path.dirname(output_path)
        visuals = os.path.join(rep, "nb_bg.mp4")
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                        f"gradients=s={wh}:c0=0x101830:c1=0x000000:d=10", "-t", "10",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", visuals], capture_output=True, timeout=60)

    # 2. Editor montajı: NotebookLM sesi + görsel(pan) — altyazı opsiyonel (ses zaten EN net)
    if crew:
        out = crew.editor.montage(visuals, audio_path, output_path, vertical=vertical,
                                  voice_boost=False, kenburns=True)
    else:
        out = None
    if out and os.path.exists(out):
        return {"success": True, "path": out, "duration_sec": round(dur, 1), "audio_source": "notebooklm"}
    return {"success": False, "error": "montaj başarısız"}
