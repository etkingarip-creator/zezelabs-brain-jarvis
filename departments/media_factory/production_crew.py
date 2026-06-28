"""
Prodüksiyon Ekibi — media_factory'nin rol-tabanlı ofis çalışanları (gerçek stüdyo yapısı).

Dağınık modüller yerine NET ROLLER: her çalışan tek aşamadan sorumlu, Yönetmen koordine eder.
Mevcut motorları sarar (mantık tekrarı yok) — bilhassa MONTAJ ayrı bir uzman (Editor).

Roller:
  Senarist        → senaryo/diyalog          (ask_llm + blueprint)
  Ses Mühendisi   → seslendirme + casting     (XTTS/edge, çok-ses)
  Ses Tasarımcısı → müzik + SFX               (ACE-Step)
  Görüntü Yön.    → sahne görselleri          (GLM)
  Kurgucu (Editor)→ SES+GÖRÜNTÜ MONTAJI       (ffmpeg: altyazı/miks/pan)
  Yönetmen        → ekibi koordine eder, format üretir
"""
from __future__ import annotations
import os
import subprocess
from typing import List, Dict, Optional


class VoiceEngineer:
    """Ses Mühendisi — repliği uygun motor+sesle seslendirir (XTTS doğal / edge hızlı)."""
    async def voice_line(self, text: str, out_wav: str, lang: str = "tr",
                         engine: str = "xtts", speaker: str = "", pitch: str = "+0Hz") -> bool:
        if engine == "xtts":
            from departments.media_factory import tts_engine as x
            if x.is_available() and x.synth(text, out_wav, lang=lang, speaker=speaker):
                return True
        try:  # edge fallback / hız
            import edge_tts
            v = speaker if (speaker and "Neural" in speaker) else ("tr-TR-EmelNeural" if lang == "tr" else "en-US-GuyNeural")
            await edge_tts.Communicate(text, v, pitch=pitch).save(out_wav)
            return os.path.exists(out_wav) and os.path.getsize(out_wav) > 0
        except Exception:
            return False


class SoundDesigner:
    """Ses Tasarımcısı — müzik yatağı + senaryo SFX (ACE-Step gerçek, yoksa sentez)."""
    def score(self, mood_prompt: str, out_path: str, duration: int = 30) -> Optional[str]:
        try:
            from departments.media_factory.music_engine import is_available, generate_music
            if is_available() and generate_music(mood_prompt, out_path, duration=duration, poll_timeout=150):
                return out_path
        except Exception:
            pass
        try:
            from departments.media_factory.narrated_video import _make_music_bed
            return out_path if _make_music_bed(out_path, duration) else None
        except Exception:
            return None


class Cinematographer:
    """Görüntü Yönetmeni — sahne görsellerini üretir (GLM ekonomi) ve birleştirir."""
    def __init__(self, video_pipeline):
        self.vp = video_pipeline

    async def shoot(self, scene_prompts: List[str], rep_dir: str, vertical: bool = True) -> Optional[str]:
        if not self.vp:
            return None
        import asyncio
        w, h = (1080, 1920) if vertical else (1920, 1080)
        paths = [os.path.join(rep_dir, f"crew_sc{i}.mp4") for i in range(len(scene_prompts))]

        async def _g(pr, pa):
            return await self.vp.generate(prompt=pr, output_path=pa, width=w, height=h,
                                          duration_sec=5, model="glm-5.2")
        await asyncio.gather(*[_g(scene_prompts[i], paths[i]) for i in range(len(scene_prompts))],
                             return_exceptions=True)
        ok = [p for p in paths if os.path.exists(p)]
        if not ok:
            return None
        out = os.path.join(rep_dir, "crew_concat.mp4")
        lst = os.path.join(rep_dir, "crew_list.txt")
        with open(lst, "w") as f:
            f.write("".join(f"file '{p}'\n" for p in ok))
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", out], capture_output=True, timeout=120)
        return out if os.path.exists(out) else None


class Editor:
    """Kurgucu — SES + GÖRÜNTÜ MONTAJI uzmanı. Görsel(pan) + diyalog/anlatım + müzik/SFX +
    altyazı → tek MP4. Tüm formatların montaj merkezini tek elde toplar."""
    def montage(self, visuals: str, voice: str, output: str, vertical: bool = True,
                music: str = "", sfx: str = "", ass_subs: str = "",
                voice_boost: bool = True, kenburns: bool = True) -> Optional[str]:
        if not (visuals and os.path.exists(visuals) and voice and os.path.exists(voice)):
            return None
        from departments.media_factory.narrated_video import _ffprobe_duration
        dur = _ffprobe_duration(voice)
        if dur <= 0:
            return None
        wh = "1080:1920" if vertical else "1920:1080"
        vf = f"scale={wh}:force_original_aspect_ratio=increase,crop={wh}"
        if kenburns:
            s = wh.replace(":", "x")
            vf += f",zoompan=z='min(zoom+0.0004,1.12)':d=1:s={s}:fps=25"
        if ass_subs and os.path.exists(ass_subs):
            vf += f",ass='{ass_subs.replace(chr(92), '/').replace(':', chr(92)+':')}'"
        vchain = f"[0:v]{vf}[v]"
        vexpr = "[1:a]loudnorm=I=-14,volume=1.25[vo]" if voice_boost else "[1:a]aresample=44100[vo]"
        cmd = ["ffmpeg", "-y", "-stream_loop", "-1", "-i", visuals, "-i", voice]
        amix_in, idx = ["[vo]"], 2
        extra = ""
        for layer, vol in ((music, 0.3), (sfx, 0.22)):
            if layer and os.path.exists(layer):
                cmd += ["-stream_loop", "-1", "-i", layer]
                extra += f";[{idx}:a]volume={vol},aresample=44100[a{idx}]"; amix_in.append(f"[a{idx}]"); idx += 1
        if len(amix_in) > 1:
            afilter = vexpr + extra + f";{''.join(amix_in)}amix=inputs={len(amix_in)}:duration=first:normalize=0[a]"
        else:
            afilter = vexpr.replace("[vo]", "[a]")
        cmd += ["-filter_complex", vchain + ";" + afilter, "-map", "[v]", "-map", "[a]",
                "-t", f"{dur:.2f}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", output]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=400)
        return output if r.returncode == 0 and os.path.exists(output) else None


class Director:
    """Yönetmen — ekibi (Senarist/Ses Müh./Ses Tas./Görüntü Yön./Kurgucu) koordine eder."""
    def __init__(self, agent):
        self.agent = agent
        self.voice = VoiceEngineer()
        self.sound = SoundDesigner()
        self.dop = Cinematographer(getattr(agent, "_video_pipeline", None))
        self.editor = Editor()

    def crew(self) -> Dict[str, str]:
        return {"Senarist": "ask_llm + blueprint", "Ses Mühendisi": "XTTS/edge çok-ses",
                "Ses Tasarımcısı": "ACE-Step müzik+SFX", "Görüntü Yönetmeni": "GLM sahne",
                "Kurgucu (Editor)": "ffmpeg ses+görüntü montajı", "Yönetmen": "koordinasyon"}
