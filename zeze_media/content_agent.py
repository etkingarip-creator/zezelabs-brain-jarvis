import json
import time
import os
import sys
import subprocess
import requests

# Proje köküne path ekle
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.mq_client import MQClient

SUPPORTED_SKILLS = {"youtube-content", "humanizer", "songwriting-and-ai-music"}


class ContentAgent:
    def __init__(self):
        print("[ContentAgent] ZOM Content Factory v2 başlatılıyor...")
        self.mq = MQClient()
        self.bridge_url = os.getenv("JARVIS_BRIDGE_URL", "http://jarvis_bridge:7000/query")
        self.openjarvis_root = os.getenv("OPENJARVIS_ROOT", "C:/Users/Zezelabs2/OpenJarvis")

    def _run_jarvis_skill(self, skill_name: str, params: dict) -> str:
        """OpenJarvis CLI skill'ini uv üzerinden çalıştırır."""
        try:
            result = subprocess.run(
                ["uv", "run", "python", "-m", "openjarvis.cli",
                 "skill", "run", skill_name, json.dumps(params)],
                cwd=self.openjarvis_root,
                capture_output=True, text=True, timeout=60
            )
            output = result.stdout or result.stderr
            print(f"[ContentAgent] OpenJarvis skill '{skill_name}' çalıştı.")
            return output
        except FileNotFoundError:
            print("[ContentAgent] uv/OpenJarvis bulunamadı, JARVIS_BRIDGE'e fallback.")
            return self._call_bridge(skill_name, params)
        except Exception as e:
            return f"Skill hatası: {e}"

    def _call_bridge(self, context: str, params: dict) -> str:
        """JARVIS_BRIDGE LLM üzerinden içerik üretir."""
        system_prompt = (
            "Sen bir Zezelabs İçerik Uzmanısın. ZOM standartlarında yüksek kaliteli içerik üret.\n"
            "YouTube senaryosu ise: Hook, Intro, Detaylı bölümler ve Outro ekle.\n"
            "Etsy/SEO ise: Başlık, 13 tag ve SEO uyumlu açıklama üret.\n"
            "Müzik ise: Suno/Udio için detailed prompt üret."
        )
        try:
            payload = {
                "prompt": f"{system_prompt}\n\nGörev/Bağlam: {context}\nParametreler: {json.dumps(params, ensure_ascii=False)}",
                "model": "gemini-2.5-flash",
                "force_cloud": True,
                "use_cache": True
            }
            resp = requests.post(self.bridge_url, json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json().get("response", "İçerik üretilemedi.")
        except Exception as e:
            return f"Bridge hatası: {e}"

    def _detect_skill(self, task_desc: str) -> str:
        """Görev metninden OpenJarvis skill adını otomatik algılar."""
        task_lower = task_desc.lower()
        if any(k in task_lower for k in ["youtube", "video", "senaryo", "script"]):
            return "youtube-content"
        if any(k in task_lower for k in ["insanlaştır", "humanize", "doğal", "insan"]):
            return "humanizer"
        if any(k in task_lower for k in ["müzik", "şarkı", "song", "music", "suno"]):
            return "songwriting-and-ai-music"
        return ""  # Bridge fallback

    def process_task(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            task_id = data.get("id", str(int(time.time())))
            task_desc = data.get("task", "")
            skill = data.get("skill", "") or self._detect_skill(task_desc)
            params = data.get("params", {"topic": task_desc})

            print(f"\n{'='*60}")
            print(f"[ContentAgent] Görev #{task_id} Alındı")
            print(f"[ContentAgent] Açıklama: {task_desc}")
            print(f"[ContentAgent] Skill: {skill or 'bridge-fallback'}")
            print(f"{'='*60}")

            # Üretim
            if skill in SUPPORTED_SKILLS:
                content = self._run_jarvis_skill(skill, params)
            else:
                content = self._call_bridge(task_desc, params)

            print(f"[ContentAgent] ✅ İçerik üretildi ({len(content)} karakter).")

            # Telegram'a gönder
            self.mq.publish("telegram_out_queue", {
                "type": "content_report",
                "task": (
                    f"**🎬 Zeze-Media Raporu (ID: {task_id})**\n"
                    f"**Skill:** {skill or 'bridge'}\n\n"
                    f"{content[:3000]}"
                ),
                "id": task_id,
                "agent": "content_agent"
            })
            print("[ContentAgent] 📤 Rapor telegram_out_queue'ya gönderildi.")

        except Exception as e:
            print(f"[ContentAgent] 🚫 Hata oluştu: {e}")
            import traceback
            traceback.print_exc()
            self.mq.publish("failure_reports_queue", {
                "id": data.get("id"), "error": str(e), "agent": "content_agent"
            })

    def start(self):
        self.mq.connect()
        self.mq.declare_queue("content_queue")
        self.mq.declare_queue("telegram_out_queue")
        self.mq.declare_queue("failure_reports_queue")
        self.mq.consume("content_queue", self.process_task)


if __name__ == "__main__":
    agent = ContentAgent()
    agent.start()

