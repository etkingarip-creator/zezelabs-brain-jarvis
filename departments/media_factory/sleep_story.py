"""
Sleep Story — uyku/dinlenme uzun-form içeriği (60-120dk, tarih/gizem).

Gelir gerçeği: 321 Relaxing $17k/ay, "Boring History" 6sa uyku-belgeselleri. RPM düşük
ama tek izlemede 8sa watch-time → algoritma ödüllendirir. ÜRETİM SIRRI: ses kalitesi
öncelik, görsel minimal (statik/yavaş-pan). Bizim araçlara tam uyar.

Pipeline: uzun sakin narration (edge-tts, yavaş) + ambient müzik (ACE-Step/sentez, çok
altta) + yavaş-pan görsel döngü → uzun MP4. Altyazı YOK (uyku içeriği).
"""
from __future__ import annotations
import os
import asyncio
import subprocess
import tempfile
from typing import Optional, List

SLEEP_NICHES = ["tarih (history to sleep to)", "çözülmemiş gizemler", "uzay/kozmos",
                "antik medeniyetler", "okyanus derinlikleri", "kayıp şehirler"]


async def _gen_long_script(ask_llm, topic: str, target_minutes: int, lang: str = "en") -> str:
    """Sakin, monoton-dostu uzun narration üret. ~145 kelime/dk → parça parça (uzun için döngü)."""
    target_words = target_minutes * 145
    chunks: List[str] = []
    words_so_far = 0
    prev = ""
    dil = "TÜRKÇE" if lang == "tr" else "İngilizce"
    while words_so_far < target_words:
        remaining = target_words - words_so_far
        ask = min(700, remaining)
        prompt = (
            f"Uyku/dinlenme videosu için SAKİN, monoton, yavaş tempolu anlatı yaz ({dil}). "
            f"Konu: {topic} (niş: uykuda dinlenecek tarih/gizem). ~{ask} kelime. "
            f"Heyecan/şok YOK — yumuşak, hipnotik, uyutucu akış. Bölüm başlığı/işaret yok, düz anlatı.\n"
            + (f"ÖNCEKİ KISMIN SONU (devam et, tekrarlama):\n...{prev[-300:]}" if prev else "Baştan başla.")
        )
        part = await ask_llm(prompt=prompt,
                             system_prompt="Sen uyku-hikayesi anlatıcısısın. Yumuşak, sakin, hipnotik, monoton-dostu yazarsın.")
        part = (part or "").strip()
        if not part:
            break
        chunks.append(part)
        prev = part
        words_so_far += len(part.split())
        if len(chunks) > 60:  # güvenlik
            break
    return "\n\n".join(chunks)


async def build_sleep_story(ask_llm, topic: str, output_path: str, target_minutes: int = 5,
                            visuals_video: Optional[str] = None,
                            voice: Optional[str] = None,
                            sfx_prompt: Optional[str] = None, lang: str = "en",
                            title: Optional[str] = None) -> Optional[dict]:
    # Dile göre anlatıcı sesi: TR → tr-TR-AhmetNeural (karizmatik erkek), EN → Christopher
    if voice is None:
        voice = "tr-TR-AhmetNeural" if lang == "tr" else "en-US-ChristopherNeural"
    # Karizmatik anlatıcı sesi (Christopher: sıcak/derin/özgüvenli storyteller).
    # Tarih/belgesel için alternatif: en-GB-RyanNeural (Attenborough-vari İngiliz).
    """Uyku hikayesi videosu: uzun sakin narration + ambient müzik + yavaş-pan görsel."""
    from departments.media_factory.narrated_video import _ffprobe_duration, _make_music_bed
    workdir = tempfile.mkdtemp(prefix="sleep_")

    # 1. Uzun narration
    script = await _gen_long_script(ask_llm, topic, target_minutes, lang=lang)
    if not script.strip():
        return None

    # 2. TTS — ÖNCE XTTS-v2 (doğal, yerel), yoksa edge-tts fallback.
    voice_mp3 = os.path.join(workdir, "voice.mp3")
    tts_src = "edge-tts"
    used_xtts = False
    try:
        from departments.media_factory import tts_engine as _xtts
        if _xtts.is_available():
            if _xtts.synth(script, voice_mp3, lang=lang):
                used_xtts = True
                tts_src = "xtts-v2"
    except Exception:
        pass
    if not used_xtts:
        import edge_tts
        paras = [p for p in script.split("\n\n") if p.strip()]
        audio_parts = []
        for i, p in enumerate(paras):
            ap = os.path.join(workdir, f"a{i}.mp3")
            try:
                await edge_tts.Communicate(p, voice, rate="-8%").save(ap)
                if os.path.exists(ap) and os.path.getsize(ap) > 0:
                    audio_parts.append(ap)
            except Exception:
                pass
        if not audio_parts:
            return None
        alist = os.path.join(workdir, "alist.txt")
        with open(alist, "w", encoding="utf-8") as f:
            f.write("".join(f"file '{a}'\n" for a in audio_parts))
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", alist, "-c", "copy", voice_mp3],
                       capture_output=True, timeout=120)
    dur = _ffprobe_duration(voice_mp3)
    if dur <= 0:
        return None

    # 3. Ambient müzik + senaryo SFX (ACE-Step'ten KISA üret, ffmpeg döngüle).
    music = os.path.join(workdir, "ambient.wav")
    sfx = None
    has_music = False
    music_src = "yok"
    try:
        from departments.media_factory.music_engine import is_available, generate_music
        if is_available():
            mp = os.path.join(workdir, "ace.mp3")
            if generate_music("calm ambient cinematic background music, soft warm pads, slow, dreamy, emotional",
                              mp, duration=30, poll_timeout=180):
                music, has_music, music_src = mp, True, "ace-step"
            # senaryoya uygun ses efekti / atmosfer (ayrı katman)
            sp = os.path.join(workdir, "sfx.mp3")
            if generate_music(sfx_prompt or "atmospheric ambient soundscape, soft wind, distant echoes, immersive",
                              sp, duration=30, poll_timeout=180):
                sfx = sp
    except Exception:
        pass
    if not has_music:
        has_music = _make_music_bed(music, dur)
        music_src = "sentez" if has_music else "yok"

    # 4. Görsel: sakin yavaş-pan (yoksa düz koyu zemin), uzun süreye döngü
    if not (visuals_video and os.path.exists(visuals_video)):
        # statik sakin görsel: koyu gradyan (uyku-dostu) — ffmpeg lavfi
        visuals_video = os.path.join(workdir, "bg.mp4")
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                        "gradients=s=1920x1080:c0=0x0a0a2a:c1=0x000000:d=10", "-t", "10",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", visuals_video],
                       capture_output=True, timeout=60)

    # 5. Birleştir — çok yavaş pan + narration + ambient (yatay 1920x1080 uyku formatı)
    title_filter = ""
    if title:
        safe = title.replace("'", "").replace(":", " -").replace("\\", "")
        # Başlık/hook kartı: ilk 10sn üstte, sonra kaybolur (drawtext + fade)
        title_filter = (f",drawtext=text='{safe}':fontcolor=white:fontsize=52:"
                        f"x=(w-text_w)/2:y=120:box=1:boxcolor=black@0.5:boxborderw=20:"
                        f"enable='lt(t,10)'")
    vchain = ("[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
              "zoompan=z='min(zoom+0.0002,1.10)':d=1:s=1920x1080:fps=24" + title_filter + "[v]")
    # Anlatıcı: loudnorm (net+yüksek). Müzik: duyulur arka plan. SFX: senaryo atmosferi.
    cmd = ["ffmpeg", "-y", "-stream_loop", "-1", "-i", visuals_video, "-i", voice_mp3]
    voice_f = "[1:a]loudnorm=I=-14:TP=-1.5,volume=1.3,aresample=44100[vo]"
    if has_music and sfx:
        cmd += ["-stream_loop", "-1", "-i", music, "-stream_loop", "-1", "-i", sfx,
                "-filter_complex", vchain + ";" + voice_f +
                ";[2:a]volume=0.32,aresample=44100[mu];[3:a]volume=0.22,aresample=44100[fx];"
                "[vo][mu][fx]amix=inputs=3:duration=first:normalize=0[a]"]
    elif has_music:
        cmd += ["-stream_loop", "-1", "-i", music,
                "-filter_complex", vchain + ";" + voice_f +
                ";[2:a]volume=0.32,aresample=44100[mu];[vo][mu]amix=inputs=2:duration=first:normalize=0[a]"]
    else:
        cmd += ["-filter_complex", vchain + ";" + voice_f.replace("[vo]", "[a]")]
    cmd += ["-map", "[v]", "-map", "[a]", "-t", f"{dur:.2f}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", output_path]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if r.returncode == 0 and os.path.exists(output_path):
            return {"path": output_path, "duration_sec": round(dur, 1),
                    "words": len(script.split()), "music": music_src, "tts": tts_src}
        return None
    except Exception:
        return None
    finally:
        try:
            import shutil; shutil.rmtree(workdir, ignore_errors=True)
        except Exception:
            pass
