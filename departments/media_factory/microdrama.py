"""
Microdrama — Kore-tarzı dikey kısa dizi (60-90sn bölüm, 60-80 bölümlük seri).

Pazar: $26B (2030), ReelShort $30M/ay. Format: melodram (romantizm/intikam/doğaüstü),
cliffhanger'lı, dikey 9:16. Bizim edge: çok-karakterli XTTS sesleri (her karaktere ayrı
ses), GLM sahne, ACE-Step dramatik müzik — uçtan uca yerel.

build_episode: diyalog (karakter-atfı) → karakter-başına XTTS sesi (sıralı) → dikey sahne
+ altyazı (konuşmacı etiketli) + dramatik müzik → tek MP4.
"""
from __future__ import annotations
import os
import re
import json
import asyncio
import subprocess
import tempfile
from typing import Optional, List, Dict

# XTTS sesi havuzu (premium, yavaş — 6GB VRAM'de bölüm başına dakikalar)
VOICE_POOL = ["Damien Black", "Brenda Stern", "Viktor Eka", "Sofia Hellen",
              "Craig Gutsy", "Alison Dietlinde", "Badr Odhiambo", "Tammie Ema"]

# edge-tts çok-ses (HIZLI — mikrodrama volume için varsayılan). TR sınırlı (Ahmet/Emel),
# pitch ile karakterler ayrıştırılır. EN'de daha çok ses var.
EDGE_TR = [("tr-TR-AhmetNeural", "+0Hz"), ("tr-TR-EmelNeural", "+0Hz"),
           ("tr-TR-AhmetNeural", "-25Hz"), ("tr-TR-EmelNeural", "+20Hz")]
EDGE_EN = [("en-US-GuyNeural", "+0Hz"), ("en-US-JennyNeural", "+0Hz"),
           ("en-US-EricNeural", "+0Hz"), ("en-US-AriaNeural", "+0Hz")]


def assign_voices(characters: List[str], engine: str = "edge", lang: str = "tr") -> Dict[str, tuple]:
    pool = (EDGE_TR if lang == "tr" else EDGE_EN) if engine == "edge" else \
           [(v, "+0Hz") for v in VOICE_POOL]
    return {c: pool[i % len(pool)] for i, c in enumerate(characters)}


async def _synth_line(engine: str, text: str, out_wav: str, voice_spec, lang: str) -> bool:
    """Bir repliği seslendir. engine='edge' (hızlı) | 'xtts' (premium/yavaş)."""
    if engine == "xtts":
        from departments.media_factory import tts_engine as xtts
        return bool(xtts.synth(text, out_wav, lang=lang, speaker=voice_spec[0]))
    try:
        import edge_tts
        voice, pitch = voice_spec
        await edge_tts.Communicate(text, voice, pitch=pitch).save(out_wav)
        return os.path.exists(out_wav) and os.path.getsize(out_wav) > 0
    except Exception:
        return False


async def build_episode(ask_llm, genre: str, episode_num: int, output_path: str,
                        characters: Optional[List[str]] = None, prev_cliffhanger: str = "",
                        visuals_video: Optional[str] = None, lang: str = "tr",
                        engine: str = "edge") -> Optional[dict]:
    """Tek mikrodrama bölümü: çok-karakterli diyalog + sesler + sahne + müzik + cliffhanger.
    engine='edge' (HIZLI, volume için) | 'xtts' (premium ama 6GB VRAM'de yavaş)."""
    from departments.media_factory.narrated_video import _ffprobe_duration, _ass_time, _wrap
    work = tempfile.mkdtemp(prefix="drama_")

    # 1. DİYALOG senaryosu (karakter-atfı + cliffhanger)
    dil = "TÜRKÇE" if lang == "tr" else "İngilizce"
    prompt = (
        f"Kore-tarzı dikey mikrodrama, BÖLÜM {episode_num}, tür: {genre}. {dil} yaz. "
        f"60-90 saniye (~12-16 replik). Yüksek tempo, melodram, duygusal. "
        f"{'ÖNCEKİ BÖLÜM CLIFFHANGER: ' + prev_cliffhanger if prev_cliffhanger else 'Açılış bölümü.'} "
        f"Bölüm SONU güçlü cliffhanger ile bitmeli. SADECE JSON: "
        f'{{"characters":["isim1","isim2"],"lines":[{{"character":"isim","line":"replik"}}],"cliffhanger":"sonraki bölüm gerilimi"}}'
    )
    resp = await ask_llm(prompt=prompt, system_prompt="Sen viral mikrodrama senaristisin. Tempolu, duygusal, cliffhanger ustası.")
    try:
        data = json.loads(re.search(r'\{.*\}', resp, re.DOTALL).group(0))
        lines = data.get("lines", [])
        chars = data.get("characters") or characters or list({l.get("character") for l in lines})
        cliff = data.get("cliffhanger", "")
    except Exception:
        return None
    if not lines:
        return None

    voices = assign_voices(chars, engine=engine, lang=lang)
    default_v = (EDGE_TR if lang == "tr" else EDGE_EN)[0] if engine == "edge" else (VOICE_POOL[0], "+0Hz")

    # 2. Her replik karakterin sesiyle (sıralı), süre takibi
    seq, timings, t = [], [], 0.0
    for i, ln in enumerate(lines):
        spec = voices.get(ln.get("character", ""), default_v)
        wp = os.path.join(work, f"l{i}.wav")
        if await _synth_line(engine, ln.get("line", ""), wp, spec, lang):
            d = _ffprobe_duration(wp)
            if d > 0:
                seq.append(wp)
                timings.append((t, t + d, ln.get("character", ""), ln.get("line", "")))
                t += d
    if not seq:
        return None
    voice_mp3 = os.path.join(work, "dialogue.mp3")
    al = os.path.join(work, "al.txt")
    with open(al, "w", encoding="utf-8") as f:
        f.write("".join(f"file '{p}'\n" for p in seq))
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", al, "-c:a", "libmp3lame", voice_mp3],
                   capture_output=True, timeout=120)
    total = _ffprobe_duration(voice_mp3)

    # 3. Altyazı (ASS) — konuşmacı etiketli, dikey
    ass = os.path.join(work, "subs.ass")
    header = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\n\n"
              "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginV\n"
              "Style: D,Arial,54,&H00FFFFFF,&H00000000,1,1,4,2,2,300\n\n[Events]\n"
              "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    ev = []
    for (s, e, ch, line) in timings:
        txt = (f"{{\\b1}}{ch}:{{\\b0}} " + _wrap(line, 22)) if ch else _wrap(line, 22)
        ev.append(f"Dialogue: 0,{_ass_time(s)},{_ass_time(e)},D,,0,0,0,,{txt}")
    with open(ass, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(ev) + "\n")

    # 4. Dramatik müzik (ACE-Step)
    music, has_music = os.path.join(work, "m.wav"), False
    try:
        from departments.media_factory.music_engine import is_available as _ma, generate_music as _gm
        if _ma() and _gm("tense dramatic emotional cinematic background music, suspenseful", music, duration=30, poll_timeout=150):
            has_music = True
    except Exception:
        pass

    # 5. Görsel (yoksa koyu sinematik zemin)
    if not (visuals_video and os.path.exists(visuals_video)):
        visuals_video = os.path.join(work, "bg.mp4")
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "gradients=s=1080x1920:c0=0x1a0a1a:c1=0x000000:d=8",
                        "-t", "8", "-c:v", "libx264", "-pix_fmt", "yuv420p", visuals_video], capture_output=True, timeout=60)

    # 6. Montaj — dikey + altyazı + diyalog + müzik
    ass_esc = ass.replace("\\", "/").replace(":", "\\:")
    vchain = ("[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
              f"ass='{ass_esc}'[v]")
    cmd = ["ffmpeg", "-y", "-stream_loop", "-1", "-i", visuals_video, "-i", voice_mp3]
    if has_music:
        cmd += ["-stream_loop", "-1", "-i", music,
                "-filter_complex", vchain + ";[1:a]loudnorm=I=-14,volume=1.2[vo];[2:a]volume=0.22[mu];"
                "[vo][mu]amix=inputs=2:duration=first:normalize=0[a]"]
    else:
        cmd += ["-filter_complex", vchain + ";[1:a]loudnorm=I=-14,volume=1.2[a]"]
    cmd += ["-map", "[v]", "-map", "[a]", "-t", f"{total:.2f}", "-c:v", "libx264",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", output_path]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if r.returncode == 0 and os.path.exists(output_path):
            return {"path": output_path, "episode": episode_num, "duration_sec": round(total, 1),
                    "characters": chars, "voices": voices, "lines": len(lines), "cliffhanger": cliff}
        return None
    finally:
        try:
            import shutil; shutil.rmtree(work, ignore_errors=True)
        except Exception:
            pass
