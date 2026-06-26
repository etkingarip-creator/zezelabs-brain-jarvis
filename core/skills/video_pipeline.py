"""
ZezeLabs Holding OS — VideoPipeline
3 Katmanlı Gerçek MP4 Video Üretim Motoru

Katman 1: fal.ai (wan2.1) — FAL_AI_KEY gerekli, $20 ücretsiz kredi
Katman 2: Replicate (wan2.1-1.3b) — REPLICATE_API_TOKEN gerekli
Katman 3: ffmpeg + Pollinations frame'leri — Her zaman ücretsiz, ffmpeg 8.1.1+ gerekli

Tüm katmanlar asyncio.to_thread ile non-blocking çalışır.
"""
import os
import io
import time
import asyncio
import logging
import subprocess
import tempfile
import shutil
import re
from typing import Optional
from pathlib import Path

logger = logging.getLogger("zom.skills.video_pipeline")

# Aspect ratio → (width, height) → ffmpeg scale/pad filtresi
ASPECT_CONFIGS = {
    "9:16":  (1080, 1920),   # TikTok / Reels / Shorts (dikey)
    "16:9":  (1920, 1080),   # YouTube uzun format (yatay)
    "1:1":   (1080, 1080),   # Instagram kare
    "4:5":   (1080, 1350),   # Instagram portre
}


def _detect_aspect(width: int, height: int) -> str:
    """Piksel boyutlarından aspect ratio string'i çıkar."""
    if height > width:
        return "9:16"
    elif width > height:
        return "16:9"
    return "1:1"


class VideoPipeline:
    """
    3 Katmanlı gerçek MP4 üretim motoru.

    Kullanım:
        pipeline = VideoPipeline()
        path = await pipeline.generate(
            prompt="Dramatik bir sahne...",
            output_path="reports/task_id/video.mp4",
            width=1080, height=1920,
            duration_sec=15
        )
    """

    def __init__(self):
        self.fal_key = os.getenv("FAL_AI_KEY") or os.getenv("FAL_KEY")
        self.replicate_token = os.getenv("REPLICATE_API_TOKEN")
        self._ffmpeg_available = self._check_ffmpeg()

    def _check_ffmpeg(self) -> bool:
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _parse_scenes(self, prompt: str) -> List[str]:
        """
        Senaryo metninden görsel sahneleri (prompt'ları) ayıklar.
        [Sahne 1], [Görsel 1], Scene 1: gibi yapıları veya paragrafları bulur.
        """
        # 1. Regex ile Sahne/Görsel/Visual bloklarını yakala
        patterns = [
            r"(?i)(?:sahne|görsel|visual|scene)\s*\d+[:\-\s]*(.*?)(?=(?:sahne|görsel|visual|scene)\s*\d+|\Z)",
            r"\[(?:sahne|görsel|visual|scene)\s*\d+\][:\-\s]*(.*?)(?=\[(?:sahne|görsel|visual|scene)\s*\d+\]|\Z)",
            r"\((?:sahne|görsel|visual|scene)\s*\d+\)[:\-\s]*(.*?)(?=\((?:sahne|görsel|visual|scene)\s*\d+\)|\Z)"
        ]
        
        scenes = []
        for pattern in patterns:
            found = re.findall(pattern, prompt, flags=re.DOTALL)
            if found:
                # Temizle ve boş olmayanları ekle
                scenes = [s.strip() for s in found if s.strip()]
                break
                
        # Eğer regex ile bulunamadıysa paragraflara böl
        if not scenes:
            paragraphs = prompt.split("\n")
            for p in paragraphs:
                p_clean = p.strip()
                # Markdown başlıklarını veya çok kısa satırları ele
                if p_clean and not p_clean.startswith("#") and len(p_clean) > 15:
                    scenes.append(p_clean)
                    
        # Max 5 sahne ile sınırla (performans için)
        return scenes[:5] if scenes else [prompt]

    async def _generate_multi_scene(
        self,
        scenes: List[str],
        output_path: str,
        width: int,
        height: int,
        total_duration: int,
        model: Optional[str],
    ) -> str:
        """Birden fazla sahneyi üretip ffmpeg concat ile birleştirir."""
        clip_paths = []
        tmp_dir = tempfile.mkdtemp(prefix="zezelabs_stitch_")
        
        try:
            duration_per_clip = max(3, total_duration // len(scenes))
            for i, scene_prompt in enumerate(scenes):
                clip_path = os.path.join(tmp_dir, f"clip_{i:04d}.mp4")
                # Her sahneyi tekil bir video olarak üret
                res_path = await self._generate_single_clip(
                    scene_prompt, clip_path, width, height, duration_per_clip, model
                )
                if res_path and os.path.exists(clip_path):
                    clip_paths.append(clip_path)
            
            if not clip_paths:
                # Hiç klip üretilemediyse, fallback
                return await self._generate_single_clip(
                    " ".join(scenes), output_path, width, height, total_duration, model
                )
                
            # ffmpeg concat demuxer ile birleştir
            concat_txt_path = os.path.join(tmp_dir, "inputs.txt")
            with open(concat_txt_path, "w", encoding="utf-8") as f:
                for cp in clip_paths:
                    safe_path = cp.replace("\\", "/")
                    f.write(f"file '{safe_path}'\n")
                    
            cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_txt_path,
                "-c", "copy",
                "-y",
                output_path
            ]
            
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if proc.returncode == 0 and os.path.exists(output_path):
                size_kb = os.path.getsize(output_path) // 1024
                return f"Stitched {len(clip_paths)} clips into single video → {output_path} ({size_kb}KB)"
            else:
                logger.error(f"ffmpeg concat failure: {proc.stderr}")
                # concat başarısız olursa ilk başarılı klibi kopyala
                shutil.copy(clip_paths[0], output_path)
                return f"Stitch failed (fallback to first clip) → {output_path}"
                
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def _try_zhipu_api(self, prompt: str, output_path: str, aspect: str, duration_sec: int) -> Optional[str]:
        """GLM/Z.ai (CogVideoX) video API. Mevcut Z.ai anahtarını (ZENMUX_API_KEY) Z.ai
        video endpoint'iyle kullanır; ayrı ZHIPU_API_KEY (bigmodel.cn) varsa onu tercih eder."""
        zhipu_key = os.getenv("ZHIPU_API_KEY")
        zai_key = os.getenv("ZENMUX_API_KEY") or os.getenv("ZAI_API_KEY")
        if zhipu_key:
            base = "https://open.bigmodel.cn/api/paas/v4"
            key = zhipu_key
        elif zai_key:
            base = os.getenv("ZAI_VIDEO_BASE", "https://api.z.ai/api/paas/v4")
            key = zai_key
        else:
            return None
        try:
            import requests as _req
            url = f"{base}/videos/generations"
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            body = {
                "model": os.getenv("ZAI_VIDEO_MODEL", "cogvideox-3"),
                "prompt": prompt,
                "quality": "quality",
                "with_audio": True,  # ürün finali için sesli (Z.ai destekliyor)
                "size": "1080x1920" if aspect == "9:16" else "1920x1080",
                "duration": min(max(int(duration_sec), 5), 10),
            }
            resp = _req.post(url, json=body, headers=headers, timeout=20)
            if resp.status_code != 200:
                logger.warning(f"GLM/Z.ai video submit failed: {resp.text[:200]}")
                return None

            task_id = resp.json().get("id")
            if not task_id:
                return None

            # Poll status — Z.ai sonuç endpoint'i /async-result/{id} (bigmodel.cn: /videos/generations/{id})
            if "z.ai" in base:
                status_url = f"{base}/async-result/{task_id}"
            else:
                status_url = f"{base}/videos/generations/{task_id}"
            for attempt in range(24):  # Max 4 dakika (cogvideox-3 ~2-3dk sürebilir)
                time.sleep(10)
                status_resp = _req.get(status_url, headers=headers, timeout=15)
                if status_resp.status_code == 200:
                    result = status_resp.json()
                    task_status = result.get("task_status")
                    if task_status == "SUCCESS":
                        vr = result.get("video_result") or [{}]
                        video_url = vr[0].get("url") if vr else None
                        if video_url:
                            dl_resp = _req.get(video_url, timeout=90)
                            if dl_resp.status_code == 200:
                                with open(output_path, "wb") as f:
                                    f.write(dl_resp.content)
                                return f"Video generated via GLM/Z.ai CogVideoX → {output_path}"
                    elif task_status in ("FAIL", "CANCELLED"):
                        logger.warning(f"GLM/Z.ai video task failed: {task_status}")
                        return None
            logger.warning("GLM/Z.ai video poll timeout (4dk)")
            return None
        except Exception as e:
            logger.warning(f"GLM/Z.ai video API error: {e}")
            return None

    def _try_higgsfield_api(self, prompt: str, output_path: str, aspect: str) -> Optional[str]:
        """Higgsfield Video API'sini çağırır."""
        higgs_key = os.getenv("HIGGSFIELD_API_KEY")
        if not higgs_key:
            return None
        try:
            import requests as _req
            url = "https://api.higgsfield.ai/v1/video/generate"
            headers = {
                "Authorization": f"Bearer {higgs_key}",
                "Content-Type": "application/json"
            }
            body = {
                "prompt": prompt,
                "aspect_ratio": aspect,
                "motion": "medium"
            }
            resp = _req.post(url, json=body, headers=headers, timeout=15)
            if resp.status_code == 200:
                video_url = resp.json().get("video_url")
                if video_url:
                    dl_resp = _req.get(video_url, timeout=60)
                    if dl_resp.status_code == 200:
                        with open(output_path, "wb") as f:
                            f.write(dl_resp.content)
                        return f"Video generated via Higgsfield API → {output_path}"
            return None
        except Exception as e:
            logger.warning(f"Higgsfield API error: {e}")
            return None

    async def _generate_single_clip(
        self,
        prompt: str,
        output_path: str,
        width: int,
        height: int,
        duration_sec: int,
        model: Optional[str] = None,
    ) -> str:
        """Tekil bir klip üretir (eski generate metodunun gövdesi)."""
        aspect = _detect_aspect(width, height)
        
        # 1. Zhipu AI (GLM) API doğrudan entegrasyonu
        if model == "glm-5.2" and os.getenv("ZHIPU_API_KEY"):
            result = await asyncio.to_thread(
                self._try_zhipu_api, prompt, output_path, aspect, duration_sec
            )
            if result:
                logger.info(f"[Zhipu API] başarılı: {output_path}")
                return result

        # 2. Higgsfield API doğrudan entegrasyonu
        if model == "higgsfield" and os.getenv("HIGGSFIELD_API_KEY"):
            result = await asyncio.to_thread(
                self._try_higgsfield_api, prompt, output_path, aspect
            )
            if result:
                logger.info(f"[Higgsfield API] başarılı: {output_path}")
                return result

        # Katman 1: fal.ai
        if self.fal_key:
            result = await asyncio.to_thread(
                self._try_fal_ai, prompt, output_path, aspect, duration_sec, model
            )
            if result:
                logger.info(f"[Katman 1] fal.ai başarılı: {output_path}")
                return result

        # Katman 2: Replicate
        if self.replicate_token:
            result = await asyncio.to_thread(
                self._try_replicate, prompt, output_path, width, height, duration_sec, model
            )
            if result:
                logger.info(f"[Katman 2] Replicate başarılı: {output_path}")
                return result

        # Katman 3: ffmpeg (her zaman ücretsiz)
        if self._ffmpeg_available:
            result = await asyncio.to_thread(
                self._ffmpeg_compose, prompt, output_path, width, height
            )
            if result:
                logger.info(f"[Katman 3] ffmpeg başarılı: {output_path}")
                return result

        # Hiçbiri çalışmadıysa Pillow GIF fallback (son çare)
        result = await asyncio.to_thread(
            self._pillow_gif_fallback, prompt, output_path, width, height
        )
        logger.warning(f"[Fallback] Pillow GIF kullanıldı: {output_path}")
        return result

    async def generate(
        self,
        prompt: str,
        output_path: str,
        width: int = 1080,
        height: int = 1920,
        duration_sec: int = 15,
        model: Optional[str] = None,
    ) -> str:
        """Ana üretim metodu — çoklu sahne veya tekil klip üretir."""
        output_path = os.path.realpath(output_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # .mp4 uzantısını garanti et
        if not output_path.lower().endswith(".mp4"):
            base, _ = os.path.splitext(output_path)
            output_path = f"{base}.mp4"

        # Eğer prompt birden fazla sahne içeriyorsa stitching yap
        scenes = self._parse_scenes(prompt)
        if len(scenes) > 1:
            logger.info(f"Multi-scene script detected. Stitching {len(scenes)} scenes.")
            return await self._generate_multi_scene(scenes, output_path, width, height, duration_sec, model)

        return await self._generate_single_clip(prompt, output_path, width, height, duration_sec, model)

    # ────────────────────────────────────────────────────────────────
    # Katman 1: fal.ai
    # ────────────────────────────────────────────────────────────────
    def _try_fal_ai(
        self, prompt: str, output_path: str, aspect: str, duration_sec: int, model: Optional[str] = None
    ) -> Optional[str]:
        """fal.ai video API — model bazlı yönlendirme ile gerçek MP4 üretir."""
        try:
            import fal_client  # pip install fal-client
        except ImportError:
            logger.debug("fal-client kurulu değil, Katman 1 atlanıyor.")
            return None

        try:
            import os as _os
            _os.environ["FAL_KEY"] = self.fal_key

            # Model bazlı endpoint eşleme
            endpoint = "fal-ai/wan/v2.1/t2v/480p"
            if model == "glm-5.2":
                endpoint = "fal-ai/cogvideox-5b"
            elif model == "higgsfield":
                endpoint = "fal-ai/ltx-video"
            elif model == "ltx-2":
                endpoint = "fal-ai/ltx-video"

            result = fal_client.run(
                endpoint,
                arguments={
                    "prompt": prompt,
                    "aspect_ratio": aspect,
                    "duration": str(min(duration_sec, 10)),  # max 10s
                    "num_inference_steps": 30,
                    "seed": 42,
                },
            )

            video_url = None
            if isinstance(result, dict):
                video_url = (
                    result.get("video", {}).get("url")
                    or result.get("output", {}).get("url")
                    or result.get("url")
                )

            if not video_url:
                logger.warning(f"fal.ai ({endpoint}): video URL alınamadı.")
                return None

            # İndir
            import requests as _req
            resp = _req.get(video_url, timeout=60)
            if resp.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                return f"Video generated via fal.ai ({endpoint}) → {output_path} ({len(resp.content)//1024}KB)"

        except Exception as e:
            logger.warning(f"fal.ai hatası: {e}")
        return None

    # ────────────────────────────────────────────────────────────────
    # Katman 2: Replicate
    # ────────────────────────────────────────────────────────────────
    def _try_replicate(
        self,
        prompt: str,
        output_path: str,
        width: int,
        height: int,
        duration_sec: int,
        model: Optional[str] = None,
    ) -> Optional[str]:
        """Replicate video API — model bazlı yönlendirme ile gerçek MP4 üretir."""
        try:
            import replicate  # pip install replicate
        except ImportError:
            logger.debug("replicate kurulu değil, Katman 2 atlanıyor.")
            return None

        try:
            import os as _os
            _os.environ["REPLICATE_API_TOKEN"] = self.replicate_token

            aspect_ratio = "9:16" if height > width else "16:9"

            # Model bazlı endpoint eşleme
            endpoint = "wan-video/wan-2.1-1.3b"
            if model == "glm-5.2":
                endpoint = "lucataco/cogvideox-5b"
            elif model == "higgsfield":
                endpoint = "lightricks/ltx-video"
            elif model == "ltx-2":
                endpoint = "lightricks/ltx-video"

            input_dict = {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
            }
            
            if "ltx-video" in endpoint:
                input_dict["num_frames"] = 25
            else:
                input_dict["duration"] = min(duration_sec, 5)
                input_dict["num_frames"] = 81

            output = replicate.run(
                endpoint,
                input=input_dict,
            )

            # output genellikle URL listesi veya tek URL
            video_url = None
            if isinstance(output, list) and output:
                video_url = str(output[0])
            elif isinstance(output, str):
                video_url = output

            if not video_url:
                return None

            import requests as _req
            resp = _req.get(video_url, timeout=60)
            if resp.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                return f"Video generated via Replicate ({endpoint}) → {output_path} ({len(resp.content)//1024}KB)"

        except Exception as e:
            logger.warning(f"Replicate hatası: {e}")
        return None

    # ────────────────────────────────────────────────────────────────
    # Katman 3: ffmpeg + Pollinations görselleri (her zaman ücretsiz)
    # ────────────────────────────────────────────────────────────────
    def _ffmpeg_compose(
        self, prompt: str, output_path: str, width: int, height: int
    ) -> Optional[str]:
        """
        Pollinations.ai'dan frame görseller indirir, ffmpeg ile gerçek MP4 üretir.
        ffmpeg 8.1.1+ gerekli — kurulu olduğu doğrulandı.
        """
        try:
            import requests as _req

            tmp_dir = tempfile.mkdtemp(prefix="zezelabs_video_")
            try:
                # 8 frame indir (4 fps × 2 saniye = 8 frame → yavaş slideshow effect)
                num_frames = 8
                seeds = [101, 102, 103, 104, 201, 202, 203, 204]
                downloaded = 0

                for i, seed in enumerate(seeds):
                    frame_prompt = (
                        f"{prompt}, cinematic scene, frame {i+1}, "
                        f"high quality, dramatic lighting"
                    )
                    encoded = _req.utils.quote(frame_prompt)
                    url = (
                        f"https://image.pollinations.ai/prompt/{encoded}"
                        f"?width={min(width, 512)}&height={min(height, 512)}"
                        f"&model=flux&seed={seed}&nologo=true"
                    )

                    frame_path = os.path.join(tmp_dir, f"frame_{i+1:04d}.jpg")
                    for attempt in range(2):
                        try:
                            resp = _req.get(url, timeout=15)
                            if resp.status_code == 200:
                                with open(frame_path, "wb") as f:
                                    f.write(resp.content)
                                downloaded += 1
                                break
                            elif resp.status_code in (402, 429):
                                time.sleep(1.5)
                        except Exception:
                            time.sleep(1.0)
                    time.sleep(0.4)  # Rate limit koruması

                if downloaded < 4:
                    logger.warning(f"ffmpeg Katman 3: Yalnızca {downloaded} frame indirilebildi.")
                    # Eksik frame'leri mevcut olanlardan kopyala
                    existing = sorted(
                        [f for f in os.listdir(tmp_dir) if f.endswith(".jpg")]
                    )
                    if not existing:
                        return None
                    for i in range(num_frames):
                        fp = os.path.join(tmp_dir, f"frame_{i+1:04d}.jpg")
                        if not os.path.exists(fp):
                            src = os.path.join(tmp_dir, existing[i % len(existing)])
                            shutil.copy(src, fp)

                # ffmpeg: frame'leri MP4'e dönüştür
                # scale + pad → hedef çözünürlük, siyah kenarlık
                scale_filter = (
                    f"scale={width}:{height}:"
                    f"force_original_aspect_ratio=decrease,"
                    f"pad={width}:{height}:-1:-1:color=black"
                )

                cmd = [
                    "ffmpeg",
                    "-framerate", "2",                            # 2 fps → 4 saniye video
                    "-i", os.path.join(tmp_dir, "frame_%04d.jpg"),
                    "-vf", scale_filter,
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-crf", "23",                                 # Kalite dengesi
                    "-movflags", "+faststart",                    # Web-ready
                    "-y",                                         # Üzerine yaz
                    output_path,
                ]

                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                if proc.returncode == 0 and os.path.exists(output_path):
                    size_kb = os.path.getsize(output_path) // 1024
                    return (
                        f"Video generated via ffmpeg (Katman 3) → {output_path} "
                        f"({downloaded} frames, {size_kb}KB, {width}x{height})"
                    )
                else:
                    logger.error(f"ffmpeg hata kodu {proc.returncode}: {proc.stderr[:300]}")
                    return None

            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)

        except Exception as e:
            logger.error(f"ffmpeg Katman 3 hatası: {e}")
            return None

    # ────────────────────────────────────────────────────────────────
    # Son çare: Pillow animasyonlu GIF fallback
    # ────────────────────────────────────────────────────────────────
    def _pillow_gif_fallback(
        self, prompt: str, output_path: str, width: int, height: int
    ) -> str:
        """ffmpeg de yoksa Pillow ile animasyonlu GIF üretir. ffmpeg varsa MP4'e dönüştürür."""
        try:
            from PIL import Image, ImageDraw

            _NEON = [
                (0, 255, 204), (0, 230, 255), (255, 0, 127), (200, 0, 255),
                (255, 200, 0), (0, 180, 255), (255, 80, 0), (0, 255, 100),
            ]
            frames = []
            for f in range(4):
                img = Image.new("RGB", (width, height), "#0c0d14")
                draw = ImageDraw.Draw(img)
                for i in range(8):
                    off = i * 20 + f * 8
                    color = _NEON[i % len(_NEON)]
                    x0, x1 = min(off, width - off), max(off, width - off)
                    y0, y1 = min(off, height - off), max(off, height - off)
                    if x0 < x1 and y0 < y1:
                        draw.rectangle([x0, y0, x1, y1], outline=color, width=2)
                text = prompt[:30] + "..." if len(prompt) > 30 else prompt
                draw.text((20, height - 60), f"ZezeLabs Video | {text}", fill="#ffffff")
                draw.text((20, height - 40), f"Frame {f+1}/4", fill="#00ffcc")
                frames.append(img)

            gif_path = output_path.replace(".mp4", ".gif")
            frames[0].save(
                gif_path, save_all=True, append_images=frames[1:],
                duration=400, loop=0, format="GIF"
            )

            # ffmpeg varsa GIF'i MP4'e çevir
            if self._ffmpeg_available:
                cmd = [
                    "ffmpeg",
                    "-i", gif_path,
                    "-movflags", "+faststart",
                    "-pix_fmt", "yuv420p",
                    "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                    "-y",
                    output_path
                ]
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                if proc.returncode == 0 and os.path.exists(output_path):
                    try:
                        os.remove(gif_path)
                    except Exception:
                        pass
                    return f"Pillow GIF converted to MP4 via ffmpeg → {output_path}"

            return f"Pillow GIF fallback → {gif_path} (ffmpeg veya API bulunamadı)"
        except Exception as e:
            return f"Tüm video üretim katmanları başarısız: {e}"
