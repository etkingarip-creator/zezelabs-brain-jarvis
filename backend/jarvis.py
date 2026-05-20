import asyncio
import io
import json
import re
import logging
import os
import sys
import tempfile
import time
import threading
import subprocess
import uuid
import psutil # New dependency for system stats
from contextlib import asynccontextmanager

# 1. PATH & ZOM ENVIRONMENT (Unified Structure)
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path: sys.path.insert(0, _root)

# ── ZOM CORE IMPORTS (CLAUDE CODE PROTOCOL) ──
from core.orchestrator.router_agent import RouterAgent
from core.mq_client import MQClient
from core.security.guardrails import Guardrails

# 2. LOGGING (ZOM STANDARDS)
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(name)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(_root, "jarvis_zom_core.log"), encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("jarvis_zom")

# 3. IMPORTS
import edge_tts
import httpx
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from silero_vad import load_silero_vad, VADIterator
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
from dotenv import load_dotenv

# RabbitMQ for ZOM Integration
try:
    import pika
    HAS_RABBIT = True
    RABBIT_SKIP = False # Global skip if it fails too much
except ImportError:
    HAS_RABBIT = False
    RABBIT_SKIP = True

load_dotenv(os.path.join(_root, ".env"))

# 4. INTELLIGENCE (GEMINI 2.0 FLASH & LOCAL FIRST)
try:
    import google.generativeai as genai
    HAS_GENAI = True
    _api_key = os.getenv("GEMINI_API_KEY")
    if _api_key:
        genai.configure(api_key=_api_key)
        try:
            # Model listesini kontrol et (debug için)
            _models = [m.name.split('/')[-1] for m in genai.list_models()]
            log.info(f"💎 Gemini Bulut Hazır. Modeller: {', '.join(_models[:5])}...")
        except:
            log.info(f"💎 Gemini Bulut Bağlantısı Kuruldu.")
    else:
        HAS_GENAI = False
except ImportError:
    HAS_GENAI = False

from backend.QueryEngine import QueryEngine
from backend.tools import BashTool, FileEditTool, FileReadTool

SAMPLE_RATE   = 16000
CHUNK_SIZE    = 512 

class ConnectionManager:
    def __init__(self): 
        self.active_connections = set() # SET prevents duplicates by design
        self.sent_cache = set()
        
    async def connect(self, ws): 
        await ws.accept()
        self.active_connections.add(ws)
        log.info(f"New client connected. Total: {len(self.active_connections)}")
        
    def disconnect(self, ws): 
        if ws in self.active_connections:
            self.active_connections.remove(ws)
            log.info(f"Client disconnected. Total: {len(self.active_connections)}")
            
    async def broadcast(self, msg):
        # STRATEGIC DEDUPLICATION
        msg_json = json.dumps(msg, sort_keys=True)
        if msg.get("type") == "response":
            if msg_json in self.sent_cache: return
            self.sent_cache.add(msg_json)
            asyncio.get_event_loop().call_later(5, lambda: self.sent_cache.discard(msg_json))

        # Create a copy to avoid 'set changed size during iteration'
        for conn in list(self.active_connections):
            try: 
                await conn.send_json(msg)
            except: 
                self.active_connections.discard(conn) # Cleanup stale connections

manager = ConnectionManager()

class Ear:
    def __init__(self):
        self._iter = None; self._on = False; self._buf = []; self._vad_buf = []
        self._tlast = 0.0; self._vmsg_last = 0.0; self.loop = None; self.on_transcript = None
        self.enabled = True
        log.info("VAD Yukleniyor..."); self._vad = load_silero_vad(onnx=True)
        self._iter = VADIterator(self._vad, sampling_rate=SAMPLE_RATE)
        log.info("Whisper Yukleniyor..."); self._stt = WhisperModel("tiny", device="cpu")

    def start(self):
        def _cb(indata, f, t, status):
            if not self.enabled: return
            if self._iter is None or self.loop is None: return
            raw_chunk = indata[:, 0].astype(np.float32); peak = float(np.max(np.abs(raw_chunk)))
            if time.time() - self._vmsg_last > 0.1:
                asyncio.run_coroutine_threadsafe(manager.broadcast({"type":"volume","val":peak}), self.loop)
                self._vmsg_last = time.time()
            self._vad_buf.extend(raw_chunk)
            while len(self._vad_buf) >= CHUNK_SIZE:
                chunk = np.array(self._vad_buf[:CHUNK_SIZE], dtype=np.float32); self._vad_buf = self._vad_buf[CHUNK_SIZE:]
                res = self._iter(chunk)
                if res or (not self._on and peak > 0.03):
                    if not self._on:
                        self._on = True; self._buf = []
                        if self.loop: asyncio.run_coroutine_threadsafe(manager.broadcast({"type":"state","val":"listening"}), self.loop)
                    if self._on: self._buf.extend(chunk); self._tlast = time.time()
                elif self._on and (time.time() - self._tlast > 0.7):
                    if len(self._buf) > 2400:
                        audio = np.array(self._buf, dtype=np.float32)
                        if self.loop: asyncio.run_coroutine_threadsafe(manager.broadcast({"type":"state","val":"thinking"}), self.loop)
                        threading.Thread(target=self._stt_thread, args=(audio,), daemon=True).start()
                    else:
                        if self.loop: asyncio.run_coroutine_threadsafe(manager.broadcast({"type":"state","val":"idle"}), self.loop)
                    self._on = False; self._buf = []; self._iter.reset_states()
        self._stream = sd.InputStream(device=None, samplerate=SAMPLE_RATE, channels=1, callback=_cb)
        self._stream.start()

    def _stt_thread(self, audio):
        try:
            segs, _ = self._stt.transcribe(audio, language="tr", vad_filter=True)
            text = " ".join(s.text for s in segs).strip()
            if text:
                log.info(f"Duyulan: {text}")
                if self.loop: asyncio.run_coroutine_threadsafe(manager.broadcast({"type":"transcript","val":text}), self.loop)
                if self.on_transcript: self.on_transcript(text)
            else:
                if self.loop: asyncio.run_coroutine_threadsafe(manager.broadcast({"type":"state","val":"idle"}), self.loop)
        except Exception as e: log.error(f"STT Error: {e}")

# ── HERMES GATEWAY BACKGROUND PROCESSOR & RABBITMQ TELEMETRY BRIDGE ──
def publish_rabbitmq_event(event_type, payload):
    """Publishes system events & agent telemetry to RabbitMQ queue 'zom_telemetry_queue'."""
    if HAS_RABBIT and not RABBIT_SKIP:
        def _pub():
            try:
                conn = pika.BlockingConnection(pika.ConnectionParameters('localhost', connection_attempts=1))
                ch = conn.channel()
                ch.queue_declare(queue='zom_telemetry_queue', durable=True)
                ch.basic_publish(
                    exchange='',
                    routing_key='zom_telemetry_queue',
                    body=json.dumps({"event": event_type, "data": payload, "timestamp": time.time()})
                )
                conn.close()
            except Exception as e:
                log.error(f"RabbitMQ Telemetry Error: {e}")
        threading.Thread(target=_pub, daemon=True).start()

def trigger_github_push():
    """Triggers the push_to_github.py script otonomously in a background thread."""
    def _push():
        try:
            log.info("🚀 [PROJECT GITHUB-PUSH] GitHub'a yükleme işlemi başlatılıyor...")
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            push_script = os.path.join(base_dir, "push_to_github.py")
            if os.path.exists(push_script):
                sys.path.insert(0, base_dir)
                import push_to_github
                push_to_github.main()
                log.info("✅ [PROJECT GITHUB-PUSH] GitHub yükleme işlemi başarıyla tamamlandı.")
            else:
                log.error("❌ push_to_github.py bulunamadı!")
        except Exception as e:
            log.error(f"❌ GitHub yükleme hatası: {e}")
            
    threading.Thread(target=_push, daemon=True).start()

def purge_openclaw():
    """Otonomously purges all OpenClaw directories, files, and RabbitMQ queues (ZOM-compliant)."""
    import shutil
    log.info("🧹 [PROJECT PURGE-AND-ROUTE] OpenClaw temizliği başlatılıyor...")
    
    # 1. Purge global .openclaw directory
    openclaw_dir = os.path.expanduser("~/.openclaw")
    if os.path.exists(openclaw_dir):
        try:
            shutil.rmtree(openclaw_dir)
            log.info(f"🗑️ Global OpenClaw dizini başarıyla silindi: {openclaw_dir}")
        except Exception as e:
            log.error(f"❌ Global OpenClaw dizini silinemedi: {e}")
    else:
        log.info("ℹ️ Sistemde global OpenClaw dizini bulunamadı (zaten temiz).")
        
    # 2. Clean RabbitMQ Queues
    if HAS_RABBIT and not RABBIT_SKIP:
        try:
            conn = pika.BlockingConnection(pika.ConnectionParameters('localhost', connection_attempts=1))
            ch = conn.channel()
            queues_to_purge = [
                'openclaw_queue', 'openclaw_events', 'openclaw_telemetry', 
                'openclaw_orchestrator', 'openclaw_main', 'openclaw_orchestrator_queue'
            ]
            for q in queues_to_purge:
                try:
                    ch.queue_delete(queue=q)
                    log.info(f"🗑️ RabbitMQ OpenClaw kuyruğu silindi: {q}")
                except Exception as qe:
                    pass
            conn.close()
            log.info("✅ RabbitMQ OpenClaw kuyrukları temizlendi.")
        except Exception as e:
            log.error(f"❌ RabbitMQ OpenClaw temizlik hatası: {e}")

def launch_hermes_gateway():
    """Otonomously checks port 8642 and spawns the Hermes Gateway background process on Windows/Linux."""
    import socket
    import subprocess
    import sys
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        in_use = s.connect_ex(('127.0.0.1', 8642)) == 0
        if in_use:
            log.info("🧠 Hermes Gateway zaten çalışıyor (Port 8642 aktif).")
            return
            
    log.info("🚀 Hermes Gateway arka planda başlatılıyor...")
    try:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cli_path = os.path.join(base_dir, "scratch", "hermes-agent", "cli.py")
        cmd = [sys.executable, cli_path, "gateway"]
        
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=0x08000000 if sys.platform == "win32" else 0, # CREATE_NO_WINDOW
            close_fds=True
        )
        log.info("✅ Hermes Gateway arka plan süreci başarıyla tetiklendi.")
        publish_rabbitmq_event("hermes_gateway_started", {"status": "success", "port": 8642})
    except Exception as e:
        log.error(f"❌ Hermes Gateway başlatılamadı: {e}")
        publish_rabbitmq_event("hermes_gateway_started", {"status": "failure", "error": str(e)})

class Brain:
    def __init__(self):
        self.url = "http://localhost:11434"
        self.model = "qwen3.5:2b"
        self.status = "connecting"
        self.loop = None
        # Hermes Agent API Integration
        self.hermes_url = "http://127.0.0.1:8642/v1"
        self.hermes_api_key = os.getenv("HERMES_API_KEY", "your-secret-key")
        self.hermes_status = "offline"

    async def auto_configure(self):
        # 1. First, check if Hermes Agent API is online
        try:
            async with httpx.AsyncClient(timeout=2) as client:
                headers = {"Authorization": f"Bearer {self.hermes_api_key}"} if self.hermes_api_key else {}
                resp = await client.get(f"{self.hermes_url}/models", headers=headers)
                if resp.status_code == 200:
                    self.hermes_status = "online"
                    self.status = "online"
                    self.model = "hermes-agent"
                    log.info("🧠 Hermes Agent API Çevrimiçi! Jarvis'in Ana Beyni olarak ayarlandı.")
                    await manager.broadcast({"type": "brain_status", "val": "online", "model": "hermes-agent (API)"})
                    return True
        except Exception as e:
            log.info(f"ℹ️ Hermes Agent API bağlanılamadı (Çevrimdışı). Ollama/Gemini kontrol ediliyor.")
            self.hermes_status = "offline"

        # 2. Fallback to Ollama local tags
        try:
            async with httpx.AsyncClient(timeout=2) as client:
                resp = await client.get(f"{self.url}/api/tags")
                if resp.status_code == 200:
                    models = resp.json().get("models", [])
                    if models:
                        self.model = models[0]["name"]
                        self.status = "online"
                        await manager.broadcast({"type": "brain_status", "val": "online", "model": self.model})
                        return True
        except Exception as e:
            log.warning(f"⚠️ Local Ollama da çevrimdışı: {e}")

        # 3. Fallback to Cloud/offline state
        self.status = "offline"
        await manager.broadcast({"type": "brain_status", "val": "offline"})
        return False

    async def think(self, prompt, system="", history=None, force_cloud=False):
        history = history or []
        
        # ── PRIORITY 1: HERMES AGENT ──
        await self.auto_configure()
        if self.hermes_status == "online":
            try:
                # Strategic routing based on prompt type (Operational vs Strategic DeepSeek models)
                is_strategic = self._is_strategic(prompt)
                target_model = "deepseek/deepseek-v4-pro" if is_strategic else "deepseek/deepseek-v4-flash"
                
                log.info(f"🧠 İstek Hermes Agent Ana Beynine yönlendiriliyor (Model: {target_model})...")
                
                # Telemetry broadcast via RabbitMQ
                publish_rabbitmq_event("hermes_telemetry_start", {
                    "prompt": prompt,
                    "model": target_model,
                    "strategic": is_strategic
                })
                
                response = await self._think_hermes(prompt, system, history, model_override=target_model)
                
                publish_rabbitmq_event("hermes_telemetry_success", {
                    "prompt": prompt,
                    "response": response,
                    "model": target_model
                })
                
                return response
            except Exception as e:
                log.error(f"❌ Hermes Agent düşünme hatası: {e}. Fallback devrede.")
                publish_rabbitmq_event("hermes_telemetry_failure", {"error": str(e)})

        # ── PRIORITY 2: ZOM DOCTRINE (LOCAL FIRST / CLOUD FALLBACK) ──
        is_strategic = self._is_strategic(prompt)
        
        if not force_cloud and not is_strategic and self.status == "online" and self.hermes_status == "offline":
            try:
                return await self._think_local(prompt, system, history)
            except Exception as e:
                log.error(f"❌ Yerel Ollama düşünme hatası: {e}")

        # ── PRIORITY 3: CLOUD INTELLIGENCE (GEMINI) ──
        return await self._think_cloud(prompt, system, history)

    def _is_strategic(self, prompt: str) -> bool:
        """Determines if a prompt requires high-level intelligence."""
        keywords = ["mimari", "strateji", "karar", "architecture", "roadmap", "optimize", "analyze", "security"]
        return any(k in prompt.lower() for k in keywords)

    async def _think_hermes(self, prompt, system, history, model_override=None):
        headers = {
            "Content-Type": "application/json"
        }
        if self.hermes_api_key:
            headers["Authorization"] = f"Bearer {self.hermes_api_key}"

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        for msg in history:
            messages.append(msg)
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model_override or "deepseek/deepseek-v4-flash",
            "messages": messages,
            "temperature": 0.7
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(f"{self.hermes_url}/chat/completions", json=payload, headers=headers)
            if resp.status_code == 200:
                result = resp.json()
                return result["choices"][0]["message"]["content"]
            else:
                raise Exception(f"Hermes API Hata Döndürdü: {resp.status_code} - {resp.text}")

    async def _think_local(self, prompt, system, history):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{self.url}/api/generate", json=payload)
            if resp.status_code == 200:
                return resp.json().get("response", "")
            else:
                raise Exception(f"Ollama Hata: {resp.status_code}")

    async def _think_cloud(self, prompt, system, history):
        if not HAS_GENAI:
            return "ZOM Bulut Zekası (Gemini) şu anda kullanılamıyor. Lütfen API anahtarını kontrol edin."
        
        try:
            model = genai.GenerativeModel(model_name="gemini-2.5-flash")
            full_prompt = f"{system}\n\nKullanıcı: {prompt}" if system else prompt
            response = model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            log.error(f"❌ Gemini Düşünme Hatası: {e}")
            return f"Bulut Zekası Hatası: {e}"


brain = Brain()
ear = Ear()
engine = QueryEngine()

@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    brain.loop = loop; ear.loop = loop; ear.on_transcript = lambda t: engine_thread(t)
    
    # ── PURGE OPENCLAW remnants (PROJECT PURGE-AND-ROUTE) ──
    purge_openclaw()
    
    # ── LAUNCH HERMES GATEWAY BACKGROUND PROCESS ──
    launch_hermes_gateway()
    
    # ── OTONOMOUS GITHUB UPLOAD ──
    trigger_github_push()
    
    asyncio.create_task(brain.auto_configure())
    asyncio.create_task(system_stats_broadcaster()) # Start stats loop
    threading.Thread(target=ear.start, daemon=True).start()
    log.info("JARVIS ZOM v6.7 CORE ACTIVE.")
    yield

async def system_stats_broadcaster():
    """Broadcasts system CPU and Memory usage to UI every 5 seconds."""
    start_time = time.time()
    while True:
        try:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            uptime_sec = int(time.time() - start_time)
            uptime = f"{uptime_sec // 3600:02}:{(uptime_sec % 3600) // 60:02}:{uptime_sec % 60:02}"
            await manager.broadcast({
                "type": "stats",
                "cpu": cpu,
                "memory": mem,
                "uptime": uptime
            })
        except Exception as e:
            log.error(f"Stats Error: {e}")
        await asyncio.sleep(5)

class VoiceState:
    def __init__(self): self.enabled = True
voice_state = VoiceState()

last_msg = {"text": "", "time": 0}
engine_lock = asyncio.Lock()

def engine_thread(text):
    global last_msg
    now = time.time()
    if text == last_msg["text"] and (now - last_msg["time"]) < 2: return 
    last_msg = {"text": text, "time": now}
    if brain.loop: asyncio.run_coroutine_threadsafe(handle_engine(text), brain.loop)

async def handle_engine(text):
    if engine_lock.locked(): return
    async with engine_lock:
        # NON-BLOCKING ZOM INTEGRATION
        if HAS_RABBIT and not RABBIT_SKIP:
            def _pub():
                try:
                    conn = pika.BlockingConnection(pika.ConnectionParameters('localhost', connection_attempts=1))
                    ch = conn.channel()
                    ch.queue_declare(queue='main_orchestrator_queue', durable=True)
                    ch.basic_publish(exchange='', routing_key='main_orchestrator_queue', 
                                    body=json.dumps({"event": "jarvis_input", "text": text}))
                    conn.close()
                except: pass
            threading.Thread(target=_pub, daemon=True).start()

        prev_ear_state = ear.enabled; ear.enabled = False 
        await manager.broadcast({"type": "state", "val": "thinking"})
        try:
            response = await brain.think(text)
            if response:
                # SECURITY GUARDRAIL (Claude Code Protocol)
                guard = Guardrails()
                if "<tool_use name=\"bash\"" in response:
                    cmd_match = re.search(r'command":\s*"(.*?)"', response)
                    if cmd_match and not guard.validate_command(cmd_match.group(1)):
                        response = "🛑 GÜVENLİK İHLALİ: Tehlikeli komut engellendi. Bu işlem rapor edildi."
                
                # Clean tags for UI & Audio
                clean_text = re.sub(r"<(thinking|tool_use)>.*?</\1>", "", response, flags=re.DOTALL)
                clean_text = re.sub(r"(Thinking|Plan|Thought|Analiz):.*?\n", "", clean_text, flags=re.IGNORECASE)
                clean_text = re.sub(r"[*_`#]", "", clean_text).strip()

                # NUCLEAR BROADCAST WITH UNIQUE ID
                msg_id = str(uuid.uuid4())
                await manager.broadcast({"type": "response", "val": clean_text, "id": msg_id})
                await manager.broadcast({"type": "state", "val": "idle"})
                
                # ASYNC SPEAK (Don't block the next turn)
                if voice_state.enabled:
                    asyncio.create_task(speak(clean_text))
            else:
                await manager.broadcast({"type": "state", "val": "idle"})
        except Exception as e:
            log.error(f"Engine Error: {e}")
            await manager.broadcast({"type": "state", "val": "idle"})
        finally:
            # Race condition fix: ear is re-enabled only after EVERYTHING (including speak) is done
            ear.enabled = prev_ear_state

async def speak(text):
    if not text or not voice_state.enabled: return
    try:
        clean_text = re.sub(r'[*_`#]', '', text)
        communicate = edge_tts.Communicate(clean_text, "tr-TR-AhmetNeural")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            await communicate.save(tmp.name)
            # FFPLAY fix: Use simpler command for cross-platform or sounddevice
            # Here we wait for it to finish to prevent ear race condition
            proc = subprocess.Popen(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", tmp.name], 
                                  creationflags=0x08000000 if sys.platform == "win32" else 0)
            while proc.poll() is None: await asyncio.sleep(0.1)
            try: os.unlink(tmp.name)
            except: pass
    except Exception as e: log.error(f"TTS Error: {e}")

app = FastAPI(lifespan=lifespan)

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    await manager.broadcast({"type": "brain_status", "val": brain.status, "model": brain.model})
    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data); content = msg.get("val") or msg.get("content")
            if msg.get("type") in ["command", "chat"]: engine_thread(content)
            if msg.get("type") == "mic_toggle": ear.enabled = msg.get("val")
            if msg.get("type") == "voice_toggle": voice_state.enabled = msg.get("val")
    except WebSocketDisconnect: manager.disconnect(ws)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)
