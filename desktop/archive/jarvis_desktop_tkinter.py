import sys
import os
import warnings

# Disable HF Hub symlink warnings and suppress console warnings
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")

import math
import random
import json
import webbrowser
import threading
import asyncio
from queue import Queue, Empty

# Add project root to path for standalone execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
import httpx

from desktop.backend_launcher import BackendLauncher
from desktop.theme.colors import get_theme, HSL_PREMIUM
from desktop.sse_client import SSELogClient

# 🏛️ ZOM GÜVENLİK DUVARI: Kütüphane İthalat Fallback Mekanizması
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

class VoiceStreamer:
    def __init__(self, app_instance=None):
        self.app = app_instance
        self.pyaudio_available = PYAUDIO_AVAILABLE
        
        from core.audio.stt import TurkishSTT
        from core.audio.tts import TurkishTTS
        from desktop.voice_client import DesktopVoiceClient
        
        self.stt = TurkishSTT()
        self.tts = TurkishTTS()
        self.pcm_buffer = b""
        self.mic_active = False
        
        # Safe callback to capture chunks and measure peak amplitude
        def on_pcm(data, peak):
            if self.mic_active:
                self.pcm_buffer += data
                
        self.voice_client = DesktopVoiceClient(on_pcm_captured=on_pcm)

    def speak_welcoming(self):
        async def _speak():
            welcome_text = "Jarvis ses motoru devrede. Merkez odalar aktif. Size nasıl yardımcı olabilirim?"
            async for chunk in self.tts.stream_speak(welcome_text):
                if chunk and chunk != b"[SIMULATION]":
                    await self.voice_client.play_audio_chunk(chunk)
                    
        async def _init_client():
            await self.voice_client.start()
            await _speak()
            
        try:
            loop = asyncio.get_running_loop()
            is_running = loop.is_running()
        except RuntimeError:
            is_running = False

        if is_running:
            asyncio.create_task(_init_client())
        else:
            threading.Thread(target=lambda: asyncio.run(_init_client()), daemon=True).start()

    def start_mic_stream(self):
        self.mic_active = True
        self.pcm_buffer = b""
        self.voice_client.set_mic(True)

    def stop_mic_stream(self):
        self.mic_active = False
        self.voice_client.set_mic(False)
        
        if self.pcm_buffer:
            async def _transcribe_and_reply():
                if self.app:
                    self.app.append_log("[INFO] Konuşma çözümleniyor...")
                
                text = await self.stt.transcribe(self.pcm_buffer)
                self.pcm_buffer = b""
                
                if text:
                    if self.app:
                        self.app.root.after(0, self.app.add_chat_message, "user", text)
                        self.app.root.after(0, self.app.send_voice_text_task, text)
                else:
                    if self.app:
                        self.app.append_log("[WARNING] Konuşma algılanamadı veya çok sessiz.")
                        
            asyncio.create_task(_transcribe_and_reply())

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        bbox = self.widget.bbox("insert")
        if bbox:
            x, y, cx, cy = bbox
        else:
            x = y = cx = cy = 0
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw, 
            text=self.text, 
            justify=tk.LEFT,
            background="#0d1527", 
            foreground="#38bdf8", 
            relief=tk.SOLID, 
            borderwidth=1,
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=4,
            highlightbackground="#1c2842",
            highlightthickness=1
        )
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

class CustomSlideToggle(tk.Canvas):
    def __init__(self, parent, width=54, height=26, command=None, bg_color="#070d19", active_color="#10b981", inactive_color="#334155"):
        super().__init__(parent, width=width, height=height, bg=bg_color, highlightthickness=0, cursor="hand2")
        self.width = width
        self.height = height
        self.command = command
        self.active_color = active_color
        self.inactive_color = inactive_color
        self.state = False
        
        self.bind("<Button-1>", self.toggle)
        self.draw_toggle()

    def toggle(self, event=None):
        self.state = not self.state
        self.draw_toggle()
        if self.command:
            self.command(self.state)

    def draw_toggle(self):
        self.delete("all")
        r = self.height / 2
        # Draw capsule
        self.create_oval(0, 0, self.height, self.height, fill=self.active_color if self.state else self.inactive_color, width=0)
        self.create_oval(self.width - self.height, 0, self.width, self.height, fill=self.active_color if self.state else self.inactive_color, width=0)
        self.create_rectangle(r, 0, self.width - r, self.height, fill=self.active_color if self.state else self.inactive_color, width=0)
        
        # Draw switch circle
        pad = 2
        size = self.height - (pad * 2)
        if self.state:
            cx = self.width - r
            self.create_oval(cx - size/2, pad, cx + size/2, pad + size, fill="#ffffff", width=0)
        else:
            cx = r
            self.create_oval(cx - size/2, pad, cx + size/2, pad + size, fill="#94a3b8", width=0)

class JarvisDesktopApp:
    def __init__(self, root):
        self.root = root
        self.theme = get_theme().copy()
        
        # Standardize colors
        self.theme["background"] = "#070d19"
        self.theme["surface"] = "#0d1527"
        self.theme["border"] = "#1c2842"
        self.theme["primary"] = "#38bdf8"
        self.theme["accent"] = "#ec4899"
        self.theme["success"] = "#10b981"
        self.theme["warning"] = "#f59e0b"
        self.theme["error"] = "#ef4444"
        self.theme["text"] = "#f8fafc"
        self.theme["text_muted"] = "#64748b"

        # Window configuration (Premium Borderless)
        self.root.overrideredirect(True)
        self.root.minsize(1000, 700)
        self.root.configure(bg=self.theme["background"])
        
        # Center the window on start
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        width = 1150
        height = 760
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Drag variables
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._is_maximized = False
        self._prev_geometry = f"{width}x{height}+{x}+{y}"
        
        # Backend launcher
        self.launcher = BackendLauncher()
        
        # Log update queue for thread-safety
        self.log_queue = Queue()
        
        # State tracking
        self.voice_active = False
        self.speaker_active = True
        self.wave_phase = 0.0
        self.chart_step = 0
        self.active_panel = "dashboard"
        
        # Mouse coordinate tracking for interactive effects
        self.mouse_x = None
        self.mouse_y = None
        self.fin_mouse_x = None
        self.fin_mouse_y = None
        
        # Right-Click Context Menu for Selection Copying
        self.context_menu = tk.Menu(
            self.root, tearoff=0, bg=self.theme["surface"], fg=self.theme["text"],
            activebackground=self.theme["primary"], activeforeground=self.theme["background"],
            font=("Segoe UI", 9)
        )
        self.context_menu.add_command(label="📋 Seçili Metni Kopyala", command=self.copy_selected_text)
        
        # Build UI
        self.setup_main_layout()
        
        # Start background SSE log client
        backend_url = f"http://{self.launcher.host}:{self.launcher.port}/api/runtime/streamlogs"
        self.sse_client = SSELogClient(url=backend_url)
        self.sse_client.start(self.on_log_received)
        
        # Start periodic UI update loops
        self.check_status()
        self.process_queue_loop()
        self.animate_loop()
        self.update_telemetry_loop()
        
        # Auto-start backend if it's offline (unified on port 5000)
        def auto_start_worker():
            import time
            time.sleep(1.0)
            status = self.launcher.health_check()
            if status["status"] != "online":
                self.launcher.start_backend()
                self.check_status()
        threading.Thread(target=auto_start_worker, daemon=True).start()
        
        self.hovered_node = None
        self.voice_streamer = VoiceStreamer(self)
        self.voice_streamer.speak_welcoming()
        
        # Clean shutdown handling
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_main_layout(self):
        # --- CUSTOM TITLE BAR ---
        self.title_bar = tk.Frame(self.root, bg=self.theme["surface"], height=48, highlightthickness=0)
        self.title_bar.pack(fill=tk.X, side=tk.TOP)
        self.title_bar.pack_propagate(False)
        
        # Drag hooks
        self.title_bar.bind("<Button-1>", self.on_drag_start)
        self.title_bar.bind("<B1-Motion>", self.on_drag_motion)
        
        title_lbl = tk.Label(
            self.title_bar,
            text="⚡ ZEZELABS HOLDING  |  JARVIS  |  v4.1.0-Ignition",
            font=("Segoe UI", 10, "bold"),
            bg=self.theme["surface"],
            fg=self.theme["primary"]
        )
        title_lbl.pack(side=tk.LEFT, padx=20)
        title_lbl.bind("<Button-1>", self.on_drag_start)
        title_lbl.bind("<B1-Motion>", self.on_drag_motion)
        
        # Title bar controls on the right
        controls_frame = tk.Frame(self.title_bar, bg=self.theme["surface"])
        controls_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.min_btn = tk.Button(
            controls_frame, text="—", bg=self.theme["surface"], fg=self.theme["text_muted"],
            activebackground=self.theme["border"], activeforeground=self.theme["text"],
            font=("Segoe UI", 10, "bold"), relief="flat", bd=0, width=5, height=2, command=self.minimize_window
        )
        self.min_btn.pack(side=tk.LEFT, fill=tk.Y)
        
        self.max_btn = tk.Button(
            controls_frame, text="⬜", bg=self.theme["surface"], fg=self.theme["text_muted"],
            activebackground=self.theme["border"], activeforeground=self.theme["text"],
            font=("Segoe UI", 10, "bold"), relief="flat", bd=0, width=5, height=2, command=self.toggle_maximize
        )
        self.max_btn.pack(side=tk.LEFT, fill=tk.Y)
        
        self.close_btn = tk.Button(
            controls_frame, text="✕", bg=self.theme["surface"], fg=self.theme["text_muted"],
            activebackground=self.theme["error"], activeforeground="#ffffff",
            font=("Segoe UI", 10, "bold"), relief="flat", bd=0, width=5, height=2, command=self.close_window
        )
        self.close_btn.pack(side=tk.LEFT, fill=tk.Y)
        
        # Hover animations for window controls
        def make_title_btn_hover(btn, normal_bg, hover_bg, normal_fg, hover_fg):
            btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg, fg=hover_fg))
            btn.bind("<Leave>", lambda e: btn.config(bg=normal_bg, fg=normal_fg))

        make_title_btn_hover(self.min_btn, self.theme["surface"], self.theme["border"], self.theme["text_muted"], self.theme["text"])
        make_title_btn_hover(self.max_btn, self.theme["surface"], self.theme["border"], self.theme["text_muted"], self.theme["text"])
        make_title_btn_hover(self.close_btn, self.theme["surface"], self.theme["error"], self.theme["text_muted"], "#ffffff")
        
        # Premium Horizontal Header Gradient
        self.gradient_canvas = tk.Canvas(self.root, height=4, bg=self.theme["background"], highlightthickness=0)
        self.gradient_canvas.pack(fill=tk.X, side=tk.TOP)
        self.gradient_canvas.bind("<Configure>", self.draw_header_gradient)
        
        # --- SHELL CONTAINER ---
        shell_frame = tk.Frame(self.root, bg=self.theme["background"])
        shell_frame.pack(fill=tk.BOTH, expand=True)
        
        # 1. Left Navigation strip
        self.left_nav_strip = tk.Frame(shell_frame, bg=self.theme["surface"], width=60, highlightthickness=0)
        self.left_nav_strip.pack(side=tk.LEFT, fill=tk.Y)
        self.left_nav_strip.pack_propagate(False)
        self.build_left_nav()
        
        # 2. Main content area (with padding)
        self.content_frame = tk.Frame(shell_frame, bg=self.theme["background"])
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        self.build_dashboard_view()

    def build_left_nav(self):
        # Navigation icons & labels
        icons = [
            ("🏠", "Ana Panel"),
            ("📈", "Finansal Analiz"),
            ("💬", "Yazılı & Sesli Sohbet"),
            ("📁", "Dosya Gezgini"),
            ("⚙️", "Sistem Ayarları"),
            ("👤", "Profil Özetleri"),
            ("✕", "Programı Kapat")
        ]
        
        for i, (ico, name) in enumerate(icons):
            # Dynamic wrapper container to provide hover background highlights
            btn_box = tk.Canvas(self.left_nav_strip, width=60, height=55, bg=self.theme["surface"], highlightthickness=0, cursor="hand2")
            btn_box.pack(pady=4)
            
            # Draw standard icon centered
            text_id = btn_box.create_text(30, 27, text=ico, fill=self.theme["text_muted"], font=("Segoe UI Symbol", 16))
            
            # Set action callbacks
            def make_click_action(index):
                if index == 0:
                    return lambda e: self.switch_view("dashboard")
                elif index == 1:
                    return lambda e: self.open_matrix()
                elif index == 2:
                    return lambda e: self.switch_view("chat")
                elif index == 3:
                    return lambda e: self.open_docs()
                elif index == 6:
                    return lambda e: self.close_window()
                return lambda e: messagebox.showinfo("Bilgi", f"'{name}' paneli yakında entegre edilecek!")
                
            action_cb = make_click_action(i)
            btn_box.bind("<Button-1>", action_cb)
            btn_box.tag_bind(text_id, "<Button-1>", action_cb)
            
            # Hover bindings
            def on_nav_enter(e, canvas=btn_box, t_id=text_id):
                canvas.config(bg=self.theme["border"])
                canvas.itemconfig(t_id, fill=self.theme["primary"])
                canvas.create_line(2, 4, 2, 51, fill=self.theme["primary"], width=3, tags="glow_line")
                
            def on_nav_leave(e, canvas=btn_box, t_id=text_id):
                canvas.config(bg=self.theme["surface"])
                canvas.itemconfig(t_id, fill=self.theme["text_muted"])
                canvas.delete("glow_line")
                
            btn_box.bind("<Enter>", on_nav_enter)
            btn_box.bind("<Leave>", on_nav_leave)
            
            # Add beautiful native popup tooltips
            ToolTip(btn_box, name)

    def build_dashboard_view(self):
        self.dashboard_frame = tk.Frame(self.content_frame, bg=self.theme["background"])
        self.dashboard_frame.pack(fill=tk.BOTH, expand=True)
        
        # Grid Configuration: Col 0 (280px, Depts), Col 1 (420px, central widgets), Col 2 (expand, finance/activities)
        self.dashboard_frame.columnconfigure(0, minsize=290, weight=0)
        self.dashboard_frame.columnconfigure(1, minsize=430, weight=0)
        self.dashboard_frame.columnconfigure(2, weight=1)
        self.dashboard_frame.rowconfigure(0, weight=1)
        
        # --- COLUMN 0: DEPARTMANLAR ---
        self.col_depts = tk.Frame(self.dashboard_frame, bg=self.theme["background"])
        self.col_depts.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        depts_header = tk.Label(
            self.col_depts, text="🏛️ DEPARTMANLAR", 
            font=("Segoe UI", 11, "bold"), bg=self.theme["background"], fg=self.theme["primary"]
        )
        depts_header.pack(anchor="w", pady=(0, 10))
        
        # Department panel lists
        departments_data = [
            ("zeze_prompt", "🧠 ZEZE_PROMPT", "Prompt Mimarlığı", "AKTİF | 99% Optimize", "#06b6d4"),
            ("zeze_guard", "🛡️ ZEZE_GUARD", "Token & Bütçe", "AKTİF | ZOM KORUMALI", "#ec4899"),
            ("zeze_sec", "🛡️ ZEZE_SEC", "Siber Savunma", "AKTİF | KALKAN AÇIK", "#00f0ff"),
            ("zeze_rnd", "⚛️ ZEZE_RND", "Ar-Ge & İnovasyon", "TARANIYOR | KOKORO-82M", "#eab308"),
            ("zeze_eng", "⚙️ ZEZE_ENG", "Geliştirme", "MEŞGUL | config GÜNCEL", "#f59e0b"),
            ("crypto_trading", "📈 ZEZE_TRADING", "Otonom Al-Sat", "AKTİF | BOT ÇALIŞIYOR", "#10b981"),
            ("media_factory", "🎬 ZEZE_MEDIA", "İçerik Stüdyosu", "AKTİF | RENDERING", "#a78bfa")
        ]
        
        self.dept_widgets = {}
        for code, title, role, status_txt, color in departments_data:
            card = tk.Frame(
                self.col_depts, bg=self.theme["surface"], bd=0, 
                highlightthickness=1, highlightbackground=self.theme["border"]
            )
            card.pack(fill=tk.X, pady=2)
            
            # Interactive circle glow on the left (tighter padding & smaller canvas)
            left_canvas = tk.Canvas(card, width=36, height=52, bg=self.theme["surface"], highlightthickness=0)
            left_canvas.pack(side=tk.LEFT, padx=(8, 4))
            
            # Draw glow circle and pulsing dot centered at (18, 26)
            circle_id = left_canvas.create_oval(6, 14, 30, 38, outline=color, width=2, fill=self.theme["background"])
            dot_id = left_canvas.create_oval(14, 22, 22, 30, fill=color, width=0)
            
            # Text layout
            text_frame = tk.Frame(card, bg=self.theme["surface"])
            text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=3, padx=5)
            
            lbl_title = tk.Label(text_frame, text=title, font=("Segoe UI", 10, "bold"), bg=self.theme["surface"], fg=self.theme["text"])
            lbl_title.pack(anchor="w")
            
            lbl_role = tk.Label(text_frame, text=role, font=("Segoe UI", 8), bg=self.theme["surface"], fg=self.theme["text_muted"])
            lbl_role.pack(anchor="w")
            
            lbl_status = tk.Label(text_frame, text=status_txt, font=("Segoe UI", 8, "bold"), bg=self.theme["surface"], fg=color)
            lbl_status.pack(anchor="w")
            
            # Interactive clicks to open telemetry detailed monitoring panels
            def make_dept_callback(c_code):
                return lambda e: self.open_department_telemetry(c_code)
                
            card.bind("<Button-1>", make_dept_callback(code))
            left_canvas.bind("<Button-1>", make_dept_callback(code))
            lbl_title.bind("<Button-1>", make_dept_callback(code))
            lbl_role.bind("<Button-1>", make_dept_callback(code))
            lbl_status.bind("<Button-1>", make_dept_callback(code))
            
            # Hover bindings to simulate a glowing border highlight
            # Hover bindings to simulate a glowing border highlight
            def on_card_enter(e, widget=card, canv=left_canvas, c_id=circle_id, clr=color, t_f=text_frame, l_t=lbl_title, l_r=lbl_role, l_s=lbl_status):
                hover_bg = "#0f233a" if clr == "#38bdf8" or clr == "#00f0ff" or clr == "#06b6d4" else "#201128"
                widget.config(highlightbackground=clr, bg=hover_bg)
                canv.config(bg=hover_bg)
                t_f.config(bg=hover_bg)
                l_t.config(bg=hover_bg)
                l_r.config(bg=hover_bg)
                l_s.config(bg=hover_bg)
                canv.itemconfig(c_id, fill=clr, width=3)
                
            def on_card_leave(e, widget=card, canv=left_canvas, c_id=circle_id, t_f=text_frame, l_t=lbl_title, l_r=lbl_role, l_s=lbl_status):
                widget.config(highlightbackground=self.theme["border"], bg=self.theme["surface"])
                canv.config(bg=self.theme["surface"])
                t_f.config(bg=self.theme["surface"])
                l_t.config(bg=self.theme["surface"])
                l_r.config(bg=self.theme["surface"])
                l_s.config(bg=self.theme["surface"])
                canv.itemconfig(c_id, fill=self.theme["background"], width=2)
                
            card.bind("<Enter>", on_card_enter)
            card.bind("<Leave>", on_card_leave)
            
            self.dept_widgets[code] = {
                "card": card, "dot": dot_id, "canvas": left_canvas, 
                "lbl_status": lbl_status, "color": color, "pulse_val": 0, "pulse_dir": 1
            }
            ToolTip(card, f"{title} canlı metrik izleme panelini açmak için tıklayın")

        # --- GATEWAY CORE STATUS CARD (Integrated below departments) ---
        self.gateway_card = tk.Frame(
            self.col_depts, bg=self.theme["surface"], highlightthickness=1, highlightbackground=self.theme["border"]
        )
        self.gateway_card.pack(fill=tk.BOTH, expand=True, pady=(15, 0))
        
        gw_header = tk.Label(
            self.gateway_card, text="⚙️ SYSTEM TELEMETRY", font=("Segoe UI", 10, "bold"),
            bg=self.theme["surface"], fg=self.theme["primary"]
        )
        gw_header.pack(anchor="w", padx=15, pady=(12, 6))
        
        # 1. Gateway Status
        row_gw = tk.Frame(self.gateway_card, bg=self.theme["surface"])
        row_gw.pack(fill=tk.X, padx=15, pady=4)
        tk.Label(row_gw, text="Core Gateway:", font=("Segoe UI", 9, "bold"), bg=self.theme["surface"], fg=self.theme["text"]).pack(side=tk.LEFT)
        
        self.badge_canvas = tk.Canvas(row_gw, width=12, height=12, bg=self.theme["surface"], highlightthickness=0)
        self.badge_canvas.pack(side=tk.LEFT, padx=(8, 4))
        self.status_circle = self.badge_canvas.create_oval(1, 1, 11, 11, fill=self.theme["error"], width=0)
        
        self.status_text_lbl = tk.Label(row_gw, text="Offline", font=("Segoe UI", 9), bg=self.theme["surface"], fg=self.theme["text_muted"])
        self.status_text_lbl.pack(side=tk.LEFT)
        
        # 2. AI Mode
        row_ai = tk.Frame(self.gateway_card, bg=self.theme["surface"])
        row_ai.pack(fill=tk.X, padx=15, pady=4)
        self.ai_mode_lbl = tk.Label(row_ai, text="AI Mode: offline", font=("Segoe UI", 9), bg=self.theme["surface"], fg=self.theme["text_muted"])
        self.ai_mode_lbl.pack(side=tk.LEFT)
        
        # 3. Core Version
        row_ver = tk.Frame(self.gateway_card, bg=self.theme["surface"])
        row_ver.pack(fill=tk.X, padx=15, pady=4)
        self.version_lbl = tk.Label(row_ver, text="Core V: 4.1.0-Ignition", font=("Segoe UI", 9), bg=self.theme["surface"], fg=self.theme["text_muted"])
        self.version_lbl.pack(side=tk.LEFT)
        
        # 4. Memory Footprint
        row_mem = tk.Frame(self.gateway_card, bg=self.theme["surface"])
        row_mem.pack(fill=tk.X, padx=15, pady=4)
        self.memory_lbl = tk.Label(row_mem, text="Memory: 142.5 MB / 512 MB", font=("Segoe UI", 9), bg=self.theme["surface"], fg=self.theme["text_muted"])
        self.memory_lbl.pack(side=tk.LEFT)
        
        # Glowing horizontal track loader
        self.progress_canvas = tk.Canvas(self.gateway_card, height=3, bg=self.theme["surface"], highlightthickness=0)
        self.progress_canvas.pack(fill=tk.X, pady=(12, 10), padx=15)
        self.progress_track = self.progress_canvas.create_rectangle(0, 0, 1000, 3, fill=self.theme["border"], width=0)
        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 60, 3, fill=self.theme["primary"], width=0)
        self.progress_x = 0
        self.progress_dir = 1

        # --- COLUMN 1: CENTRAL PANEL (SINIR AĞI & VOICE) ---
        self.col_center = tk.Frame(self.dashboard_frame, bg=self.theme["background"])
        self.col_center.grid(row=0, column=1, sticky="nsew", padx=10)
        
        # A. Sinir Ağı Box
        self.net_box = tk.Frame(
            self.col_center, bg=self.theme["surface"], highlightthickness=1, highlightbackground=self.theme["border"]
        )
        self.net_box.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        net_header = tk.Frame(self.net_box, bg=self.theme["surface"])
        net_header.pack(fill=tk.X, padx=15, pady=(12, 6))
        tk.Label(
            net_header, text="⚛️ SINIR AĞI", font=("Segoe UI", 10, "bold"), bg=self.theme["surface"], fg=self.theme["primary"]
        ).pack(side=tk.LEFT)
        tk.Label(
            net_header, text="DURUM: AKTİF (11 AGENT KOŞUYOR)", font=("Segoe UI", 8, "bold"), bg=self.theme["surface"], fg=self.theme["success"]
        ).pack(side=tk.RIGHT, padx=10)
        
        # Dynamic animated neural net canvas
        self.net_canvas = tk.Canvas(self.net_box, bg=self.theme["surface"], highlightthickness=0)
        self.net_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.setup_neural_network()
        
        # B. Sesli Sohbet Box
        self.voice_box = tk.Frame(
            self.col_center, bg=self.theme["surface"], highlightthickness=1, highlightbackground=self.theme["border"]
        )
        self.voice_box.pack(fill=tk.X, side=tk.BOTTOM)
        
        voice_header = tk.Frame(self.voice_box, bg=self.theme["surface"])
        voice_header.pack(fill=tk.X, padx=15, pady=(12, 4))
        tk.Label(
            voice_header, text="🎤 SESLİ SOHBET KONTROLÜ", font=("Segoe UI", 10, "bold"), bg=self.theme["surface"], fg=self.theme["primary"]
        ).pack(side=tk.LEFT)
        
        self.voice_status_lbl = tk.Label(
            voice_header, text="DURUM: AKTİF", font=("Segoe UI", 8, "bold"), bg=self.theme["surface"], fg=self.theme["success"]
        )
        self.voice_status_lbl.pack(side=tk.RIGHT, padx=10)
        
        # Details subtext
        subtext_row = tk.Frame(self.voice_box, bg=self.theme["surface"])
        subtext_row.pack(fill=tk.X, padx=15, pady=(0, 8))
        tk.Label(
            subtext_row, text="Gecikme: <50ms | Whisper-Turbo: Dinliyor...", font=("Segoe UI", 8), bg=self.theme["surface"], fg=self.theme["text_muted"]
        ).pack(side=tk.LEFT)
        
        # Waveform Canvas
        self.wave_canvas = tk.Canvas(self.voice_box, height=85, bg=self.theme["background"], highlightthickness=0)
        self.wave_canvas.pack(fill=tk.X, padx=15, pady=5)
        
        # Controls (Microphone sliding toggle & Audio settings button)
        voice_ctrls = tk.Frame(self.voice_box, bg=self.theme["surface"])
        voice_ctrls.pack(fill=tk.X, padx=15, pady=(8, 12))
        
        tk.Label(
            voice_ctrls, text="AÇIK MİKROFON:", font=("Segoe UI", 9, "bold"), bg=self.theme["surface"], fg=self.theme["text"]
        ).pack(side=tk.LEFT)
        
        self.mic_toggle = CustomSlideToggle(
            voice_ctrls, command=self.on_mic_toggle, bg_color=self.theme["surface"],
            active_color=self.theme["primary"], inactive_color=self.theme["border"]
        )
        self.mic_toggle.pack(side=tk.LEFT, padx=10)
        
        self.settings_btn = self.create_premium_button(
            voice_ctrls, text="SES AYARLARI", command=self.open_voice_settings, 
            bg=self.theme["border"], fg=self.theme["text"]
        )
        self.settings_btn.pack(side=tk.RIGHT)

        # --- COLUMN 2: RIGHT PANEL (FINANCE & RECENT ACTIVITIES) ---
        self.col_right = tk.Frame(self.dashboard_frame, bg=self.theme["background"])
        self.col_right.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        
        # A. Finansal Veriler Box
        self.fin_box = tk.Frame(
            self.col_right, bg=self.theme["surface"], highlightthickness=1, highlightbackground=self.theme["border"]
        )
        self.fin_box.pack(fill=tk.X, pady=(0, 10))
        
        fin_header = tk.Frame(self.fin_box, bg=self.theme["surface"])
        fin_header.pack(fill=tk.X, padx=15, pady=(12, 6))
        tk.Label(
            fin_header, text="📈 FİNANSAL VERİLER", font=("Segoe UI", 10, "bold"), bg=self.theme["surface"], fg=self.theme["primary"]
        ).pack(side=tk.LEFT)
        tk.Label(
            fin_header, text="Yatırım Getirisi (ROI): %110", font=("Segoe UI", 8, "bold"), bg=self.theme["surface"], fg=self.theme["success"]
        ).pack(side=tk.RIGHT, padx=10)
        
        # KPI Details row
        kpi_row = tk.Frame(self.fin_box, bg=self.theme["surface"])
        kpi_row.pack(fill=tk.X, padx=15, pady=(0, 8))
        self.kpi_lbl = tk.Label(
            kpi_row, text="API BAKİYESİ: $1,450.00 (OPENROUTER)  |  Abonelik: Standart 2TB",
            font=("Segoe UI", 9, "bold"), bg=self.theme["surface"], fg=self.theme["text"]
        )
        self.kpi_lbl.pack(side=tk.LEFT)
        
        # Neon Green Area Line Chart
        self.fin_canvas = tk.Canvas(self.fin_box, height=85, bg=self.theme["background"], highlightthickness=0)
        self.fin_canvas.pack(fill=tk.X, padx=15, pady=(5, 12))
        self.fin_canvas.bind("<Motion>", self.on_fin_canvas_hover)
        self.fin_canvas.bind("<Leave>", self.on_fin_canvas_leave)
        
        # B. Son Aktiviteler Box (with scrollable department activities)
        self.act_box = tk.Frame(
            self.col_right, bg=self.theme["surface"], highlightthickness=1, highlightbackground=self.theme["border"]
        )
        self.act_box.pack(fill=tk.BOTH, expand=True)
        
        act_header = tk.Frame(self.act_box, bg=self.theme["surface"])
        act_header.pack(fill=tk.X, padx=15, pady=(12, 6))
        tk.Label(
            act_header, text="📋 SON AKTİVİTELER", font=("Segoe UI", 10, "bold"), bg=self.theme["surface"], fg=self.theme["primary"]
        ).pack(side=tk.LEFT)
        
        self.act_graph_canvas = tk.Canvas(act_header, width=120, height=22, bg=self.theme["surface"], highlightthickness=0)
        self.act_graph_canvas.pack(side=tk.RIGHT, padx=10)
        self.setup_mini_activity_graph()
        
        # Log feed viewer (scrollable department transaction log)
        self.act_list_frame = tk.Frame(self.act_box, bg=self.theme["surface"])
        self.act_list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 12))
        
        # Custom Scrolled Viewer styled to fit in
        self.activity_log_viewer = ScrolledText(
            self.act_list_frame, font=("Consolas", 9), bg=self.theme["background"], fg=self.theme["text"],
            bd=0, highlightthickness=0, relief="flat", wrap=tk.WORD,
            selectbackground=self.theme["primary"], selectforeground=self.theme["background"]
        )
        self.activity_log_viewer.pack(fill=tk.BOTH, expand=True)
        self.activity_log_viewer.bind("<Button-3>", self.show_context_menu)
        self.activity_log_viewer.bind("<Button-2>", self.show_context_menu)
        self.activity_log_viewer.insert(tk.END, ">>> [SYSTEM_INIT] Çekirdek ağ geçidi dinleniyor...\n")
        self.activity_log_viewer.config(state=tk.DISABLED)
        
        # Colors configure tags
        self.activity_log_viewer.tag_configure("zeze_prompt", foreground="#06b6d4", font=("Consolas", 9, "bold"))
        self.activity_log_viewer.tag_configure("zeze_guard", foreground="#ec4899", font=("Consolas", 9, "bold"))
        self.activity_log_viewer.tag_configure("zeze_sec", foreground="#00f0ff", font=("Consolas", 9, "bold"))
        self.activity_log_viewer.tag_configure("zeze_rnd", foreground="#eab308", font=("Consolas", 9, "bold"))
        self.activity_log_viewer.tag_configure("zeze_eng", foreground="#ef4444", font=("Consolas", 9, "bold"))
        self.activity_log_viewer.tag_configure("ceo", foreground="#a78bfa", font=("Consolas", 9, "bold"))

        # --- COLLAPSIBLE CONTROL DRAWER & TASK CONSOLE ---
        self.setup_control_drawer()

    def setup_control_drawer(self):
        # Footer handle toggle button
        self.drawer_expanded = False
        self.drawer_handle = tk.Button(
            self.root, text="▲ KONTROL PANELİ & GÖREV KONSOLU", font=("Segoe UI", 8, "bold"),
            bg=self.theme["surface"], fg=self.theme["text_muted"], activebackground=self.theme["border"],
            activeforeground=self.theme["primary"], relief="flat", bd=0, command=self.toggle_drawer
        )
        self.drawer_handle.pack(fill=tk.X, side=tk.BOTTOM)
        
        # The expanding drawer frame
        self.drawer_frame = tk.Frame(self.root, bg=self.theme["surface"], height=0, highlightthickness=1, highlightbackground=self.theme["border"])
        self.drawer_frame.pack_propagate(False)
        
        # Content of drawer
        drawer_content = tk.Frame(self.drawer_frame, bg=self.theme["surface"])
        drawer_content.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)
        
        drawer_content.columnconfigure(0, weight=4) # Task Input Console
        drawer_content.columnconfigure(1, weight=3) # Server Controls
        drawer_content.columnconfigure(2, weight=3) # Log output Matrix
        drawer_content.rowconfigure(0, weight=1)
        
        # 1. Left Section: Execute Task Console
        task_f = tk.Frame(drawer_content, bg=self.theme["surface"])
        task_f.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        tk.Label(
            task_f, text="⚡ EXECUTE TASK CONSOLE", font=("Segoe UI", 9, "bold"), bg=self.theme["surface"], fg=self.theme["primary"]
        ).pack(anchor="w", pady=(0, 5))
        
        entry_b = tk.Frame(task_f, bg=self.theme["background"], highlightthickness=1, highlightbackground=self.theme["border"])
        entry_b.pack(fill=tk.X, pady=(0, 8))
        
        self.input_entry = tk.Entry(
            entry_b, font=("Segoe UI", 10), bg=self.theme["background"], fg=self.theme["text"],
            bd=0, insertbackground=self.theme["text"], highlightthickness=0
        )
        self.input_entry.pack(fill=tk.X, padx=10, pady=8)
        self.input_entry.bind("<Return>", self.send_task)
        self.input_entry.insert(0, "Jarvis'e görev ver")
        self.input_entry.bind("<FocusIn>", self.on_entry_focus_in)
        self.input_entry.bind("<FocusOut>", self.on_entry_focus_out)
        
        self.send_btn = self.create_premium_button(
            task_f, text="Gönder (Dry Run)", command=self.send_task, bg=self.theme["primary"], fg=self.theme["background"]
        )
        self.send_btn.pack(fill=tk.X)
        
        # 2. Middle Section: Backend Server Controls
        ctrls_f = tk.Frame(drawer_content, bg=self.theme["surface"])
        ctrls_f.grid(row=0, column=1, sticky="nsew", padx=15)
        
        tk.Label(
            ctrls_f, text="🏛️ BACKEND CONTROLLER", font=("Segoe UI", 9, "bold"), bg=self.theme["surface"], fg=self.theme["primary"]
        ).pack(anchor="w", pady=(0, 8))
        
        self.srv_start_btn = self.create_premium_button(
            ctrls_f, text="Start Backend Server", command=self.start_backend, bg=self.theme["surface"], fg=self.theme["success"]
        )
        self.srv_start_btn.pack(fill=tk.X, pady=4)
        
        self.srv_stop_btn = self.create_premium_button(
            ctrls_f, text="Stop Backend Server", command=self.stop_backend, bg=self.theme["surface"], fg=self.theme["error"]
        )
        self.srv_stop_btn.pack(fill=tk.X, pady=4)
        
        # 3. Right Section: Task Response Matrix
        resp_f = tk.Frame(drawer_content, bg=self.theme["surface"])
        resp_f.grid(row=0, column=2, sticky="nsew", padx=(15, 0))
        
        tk.Label(
            resp_f, text="📋 TASK RESPONSE MATRIX", font=("Segoe UI", 9, "bold"), bg=self.theme["surface"], fg=self.theme["text_muted"]
        ).pack(anchor="w", pady=(0, 4))
        
        self.response_viewer = ScrolledText(
            resp_f, font=("Segoe UI", 9), bg=self.theme["background"], fg=self.theme["text"],
            bd=0, highlightthickness=1, highlightbackground=self.theme["border"], relief="flat", wrap=tk.WORD,
            selectbackground=self.theme["primary"], selectforeground=self.theme["background"]
        )
        self.response_viewer.pack(fill=tk.BOTH, expand=True)
        self.response_viewer.bind("<Button-3>", self.show_context_menu)
        self.response_viewer.bind("<Button-2>", self.show_context_menu)
        
        # Configure paragraph bubble tag layouts
        self.response_viewer.tag_configure("user_header", justify="right", foreground=self.theme["text_muted"], font=("Segoe UI", 8, "bold"), spacing1=6)
        self.response_viewer.tag_configure("user_bubble", justify="right", background="#db2777", foreground="#ffffff", font=("Segoe UI", 9, "bold"), spacing3=10, rmargin=15, lmargin1=120, lmargin2=120)
        self.response_viewer.tag_configure("jarvis_header", justify="left", foreground=self.theme["primary"], font=("Segoe UI", 8, "bold"), spacing1=6)
        self.response_viewer.tag_configure("jarvis_bubble", justify="left", background="#1e293b", foreground="#f8fafc", font=("Segoe UI", 9), spacing3=10, lmargin1=15, lmargin2=15, rmargin=120)
        self.response_viewer.tag_configure("system_alert", justify="center", foreground=self.theme["warning"], font=("Segoe UI", 8, "italic"), spacing3=6)
        
        self.response_viewer.config(state=tk.NORMAL)
        self.add_chat_message("jarvis", "Merhaba! ZEZELABS komut arayüzüne hoş geldiniz. Size nasıl yardımcı olabilirim?")

    def toggle_drawer(self):
        self.drawer_expanded = not self.drawer_expanded
        if self.drawer_expanded:
            self.drawer_frame.pack(fill=tk.X, side=tk.BOTTOM, before=self.drawer_handle)
            self.drawer_frame.config(height=170)
            self.drawer_handle.config(text="▼ KONTROL PANELİNİ & GÖREV KONSOLUNU GİZLE")
        else:
            self.drawer_frame.pack_forget()
            self.drawer_handle.config(text="▲ KONTROL PANELİ & GÖREV KONSOLU")

    def create_premium_button(self, parent, text, command, bg, fg):
        btn = tk.Button(
            parent, text=text, command=command, bg=bg, fg=fg,
            font=("Segoe UI", 9, "bold"), relief="flat", bd=0, cursor="hand2", padx=15, pady=6,
            activebackground=self.theme["border"], activeforeground=fg,
            highlightthickness=1, highlightbackground=bg
        )
        
        # Determine premium hover transition states
        if bg == self.theme["primary"]:
            h_bg = self.theme["accent"] # Neon Pink
            h_fg = "#ffffff"
            h_outline = self.theme["accent"]
        else:
            h_bg = self.theme["primary"] # Neon Turquoise/Cyan
            h_fg = self.theme["background"]
            h_outline = self.theme["primary"]
            
        def on_enter(e):
            btn.config(bg=h_bg, fg=h_fg, highlightbackground=h_outline)
        def on_leave(e):
            btn.config(bg=bg, fg=fg, highlightbackground=bg)
            
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def switch_view(self, view_name):
        self.active_panel = view_name
        self.append_log(f"[INFO] Navigating to: {view_name}")
        
        if view_name == "dashboard":
            if hasattr(self, "chat_view_frame"):
                self.chat_view_frame.pack_forget()
            if hasattr(self, "dashboard_frame"):
                self.dashboard_frame.pack(fill=tk.BOTH, expand=True)
        elif view_name == "chat":
            if hasattr(self, "dashboard_frame"):
                self.dashboard_frame.pack_forget()
            if not hasattr(self, "chat_view_frame"):
                self.build_chat_view()
            self.chat_view_frame.pack(fill=tk.BOTH, expand=True)
            self.chat_input_entry.focus_set()

    def build_chat_view(self):
        self.chat_view_frame = tk.Frame(self.content_frame, bg=self.theme["background"])
        
        # Grid Configuration: Col 0 (Chat Area), Col 1 (Quick Commands Sidebar)
        self.chat_view_frame.columnconfigure(0, weight=1)
        self.chat_view_frame.columnconfigure(1, minsize=290, weight=0)
        self.chat_view_frame.rowconfigure(0, weight=1)
        
        # --- LEFT SIDE: CHAT AREA ---
        chat_left_f = tk.Frame(self.chat_view_frame, bg=self.theme["background"])
        chat_left_f.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # 1. Header with dynamic neon look
        header_f = tk.Frame(chat_left_f, bg=self.theme["surface"], highlightthickness=1, highlightbackground=self.theme["border"])
        header_f.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            header_f, text="💬 ZOM BEYİN MERKEZİ - YAZILI SOHBET KONSOLU", 
            font=("Segoe UI", 11, "bold"), bg=self.theme["surface"], fg=self.theme["primary"]
        ).pack(side=tk.LEFT, padx=15, pady=10)
        
        tk.Label(
            header_f, text="SECURE CONNECTION: ACTIVE", 
            font=("Segoe UI", 8, "bold"), bg=self.theme["surface"], fg=self.theme["success"]
        ).pack(side=tk.RIGHT, padx=15, pady=10)
        
        # 2. Large Chat History Viewer
        self.chat_history_viewer = ScrolledText(
            chat_left_f, font=("Segoe UI", 10), bg=self.theme["surface"], fg=self.theme["text"],
            bd=0, highlightthickness=1, highlightbackground=self.theme["border"], relief="flat", wrap=tk.WORD,
            selectbackground=self.theme["primary"], selectforeground=self.theme["background"]
        )
        self.chat_history_viewer.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.chat_history_viewer.bind("<Button-3>", self.show_context_menu)
        self.chat_history_viewer.bind("<Button-2>", self.show_context_menu)
        
        # Tags for bubbles
        self.chat_history_viewer.tag_configure("user_header", justify="right", foreground=self.theme["text_muted"], font=("Segoe UI", 8, "bold"), spacing1=8)
        self.chat_history_viewer.tag_configure("user_bubble", justify="right", background="#db2777", foreground="#ffffff", font=("Segoe UI", 10, "bold"), spacing3=12, rmargin=20, lmargin1=150, lmargin2=150)
        self.chat_history_viewer.tag_configure("jarvis_header", justify="left", foreground=self.theme["primary"], font=("Segoe UI", 8, "bold"), spacing1=8)
        self.chat_history_viewer.tag_configure("jarvis_bubble", justify="left", background="#1e293b", foreground="#f8fafc", font=("Segoe UI", 10), spacing3=12, lmargin1=20, lmargin2=20, rmargin=150)
        self.chat_history_viewer.tag_configure("system_alert", justify="center", foreground=self.theme["warning"], font=("Segoe UI", 9, "italic"), spacing3=8)
        
        # Add welcome message
        self.chat_history_viewer.config(state=tk.NORMAL)
        self.chat_history_viewer.insert(tk.END, "⚡ JARVIS\n", "jarvis_header")
        self.chat_history_viewer.insert(tk.END, " Merhaba! ZOM Merkez Odası yazılı chat konsoluna bağlandınız. Buradan otonom departmanlara talimat verebilir, projeyi sorgulayabilir veya siber durum kontrolü yapabilirsiniz. Size nasıl yardımcı olabilirim?\n\n", "jarvis_bubble")
        self.chat_history_viewer.config(state=tk.DISABLED)
        
        # 3. Bottom Text Entry & Send Button
        entry_f = tk.Frame(chat_left_f, bg=self.theme["surface"], highlightthickness=1, highlightbackground=self.theme["border"])
        entry_f.pack(fill=tk.X)
        
        # Inner Frame for input to have padding
        input_container = tk.Frame(entry_f, bg=self.theme["background"], highlightthickness=1, highlightbackground=self.theme["border"])
        input_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=8)
        
        self.chat_input_entry = tk.Entry(
            input_container, font=("Segoe UI", 11), bg=self.theme["background"], fg="#ffffff",
            bd=0, insertbackground="#ffffff", highlightthickness=0
        )
        self.chat_input_entry.pack(fill=tk.X, padx=10, pady=8)
        self.chat_input_entry.bind("<Return>", self.send_main_chat_task)
        
        # Placeholder behavior
        self.chat_input_entry.insert(0, "Mesajınızı buraya yazın...")
        self.chat_input_entry.config(fg=self.theme["text_muted"])
        self.chat_input_entry.bind("<FocusIn>", lambda e: self.on_chat_entry_focus_in())
        self.chat_input_entry.bind("<FocusOut>", lambda e: self.on_chat_entry_focus_out())
        
        self.chat_send_btn = self.create_premium_button(
            entry_f, text="GÖNDER  ➔", command=self.send_main_chat_task, bg=self.theme["primary"], fg=self.theme["background"]
        )
        self.chat_send_btn.pack(side=tk.RIGHT, padx=10, pady=8, ipady=4)
        
        # --- RIGHT SIDE: SIDEBAR FOR QUICK COMMANDS ---
        chat_right_f = tk.Frame(self.chat_view_frame, bg=self.theme["background"])
        chat_right_f.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        quick_header = tk.Label(
            chat_right_f, text="⚡ HIZLI TALİMATLAR", font=("Segoe UI", 11, "bold"),
            bg=self.theme["background"], fg=self.theme["primary"]
        )
        quick_header.pack(anchor="w", pady=(0, 10))
        
        # We can add beautiful buttons/cards for Quick Commands
        commands = [
            ("📊 Projeyi Analiz Et", "Projeyi kapsamlı analiz et ve rapor hazırla. tüm ağaç yapısı, yollar ve dosyaları."),
            ("🛡️ Siber Savunma Durumu", "Siber savunma departmanı durumunu ve aktif kalkan protokollerini sorgula."),
            ("📈 Finansal Rapor Al", "Finansal departmandan en son bakiye ve otonom bütçe kullanım raporunu getir."),
            ("⚛️ Sinir Ağı Testi", "Otonom karar alma sinir ağının canlı gecikme ve doğruluk oranlarını test et."),
            ("⚙️ Sistem Sağlık Kontrolü", "ZOM mimarisindeki tüm mikroservis ve ajanların sağlık durumlarını listele."),
            ("🧹 Eski Logları Temizle", "Eski log dosyalarını ve diğer gereksiz yedekleri güvenli bir şekilde arşivle.")
        ]
        
        for name, cmd_txt in commands:
            card = tk.Frame(
                chat_right_f, bg=self.theme["surface"], bd=0, 
                highlightthickness=1, highlightbackground=self.theme["border"], cursor="hand2"
            )
            card.pack(fill=tk.X, pady=4)
            
            lbl_name = tk.Label(card, text=name, font=("Segoe UI", 9, "bold"), bg=self.theme["surface"], fg=self.theme["text"], cursor="hand2")
            lbl_name.pack(anchor="w", padx=12, pady=(8, 2))
            
            lbl_desc = tk.Label(
                card, text=cmd_txt, font=("Segoe UI", 8), 
                bg=self.theme["surface"], fg=self.theme["text_muted"], wrap=250, justify=tk.LEFT, cursor="hand2"
            )
            lbl_desc.pack(anchor="w", padx=12, pady=(0, 8))
            
            # Clicking the card automatically populates the text field and runs it
            def make_cmd_callback(text=cmd_txt):
                return lambda e: self.run_quick_command(text)
                
            card.bind("<Button-1>", make_cmd_callback())
            lbl_name.bind("<Button-1>", make_cmd_callback())
            lbl_desc.bind("<Button-1>", make_cmd_callback())
            
            # Hover highlight glow
            def on_cmd_enter(e, c=card, l_n=lbl_name, l_d=lbl_desc):
                c.config(highlightbackground=self.theme["accent"], bg="#1c0d24")
                l_n.config(bg="#1c0d24", fg=self.theme["accent"])
                l_d.config(bg="#1c0d24")
            def on_cmd_leave(e, c=card, l_n=lbl_name, l_d=lbl_desc):
                c.config(highlightbackground=self.theme["border"], bg=self.theme["surface"])
                l_n.config(bg=self.theme["surface"], fg=self.theme["text"])
                l_d.config(bg=self.theme["surface"])
                
            card.bind("<Enter>", on_cmd_enter)
            card.bind("<Leave>", on_cmd_leave)
            
            ToolTip(card, "Bu talimatı hemen göndermek için tıklayın")

    def run_quick_command(self, text):
        self.chat_input_entry.delete(0, tk.END)
        self.chat_input_entry.config(fg="#ffffff")
        self.chat_input_entry.insert(0, text)
        self.send_main_chat_task()

    def on_chat_entry_focus_in(self):
        if self.chat_input_entry.get() == "Mesajınızı buraya yazın...":
            self.chat_input_entry.delete(0, tk.END)
            self.chat_input_entry.config(fg="#ffffff")
            
    def on_chat_entry_focus_out(self):
        if not self.chat_input_entry.get():
            self.chat_input_entry.insert(0, "Mesajınızı buraya yazın...")
            self.chat_input_entry.config(fg=self.theme["text_muted"])

    def add_main_chat_message(self, sender, text):
        self.chat_history_viewer.config(state=tk.NORMAL)
        if sender == "user":
            self.chat_history_viewer.insert(tk.END, "👤 KULLANICI\n", "user_header")
            self.chat_history_viewer.insert(tk.END, f"  {text}   ⚡  \n\n", "user_bubble")
        elif sender == "jarvis":
            self.chat_history_viewer.insert(tk.END, "⚡ JARVIS\n", "jarvis_header")
            self.chat_history_viewer.insert(tk.END, f"  {text}  \n\n", "jarvis_bubble")
        else: # system
            self.chat_history_viewer.insert(tk.END, f"⚠️ {text}\n\n", "system_alert")
        self.chat_history_viewer.see(tk.END)
        self.chat_history_viewer.config(state=tk.DISABLED)

    def send_main_chat_task(self, event=None):
        task = self.chat_input_entry.get()
        if not task or task == "Mesajınızı buraya yazın...":
            messagebox.showwarning("Uyarı", "Lütfen geçerli bir görev girin.")
            return
            
        self.add_main_chat_message("user", task)
        self.chat_input_entry.delete(0, tk.END)
        
        # Show "thinking..." status bubbles in Chat
        self.chat_history_viewer.config(state=tk.NORMAL)
        thinking_index = self.chat_history_viewer.index(tk.END + "-1c")
        self.chat_history_viewer.insert(tk.END, "⚡ JARVIS: Düşünüyor...\n", "jarvis_header")
        self.chat_history_viewer.insert(tk.END, " • • • \n\n", "jarvis_bubble")
        self.chat_history_viewer.see(tk.END)
        self.chat_history_viewer.config(state=tk.DISABLED)
        
        # Start a background thread to send the HTTP post request asynchronously
        threading.Thread(target=self._async_send_main_task, args=(task, thinking_index), daemon=True).start()

    def _async_send_main_task(self, task, thinking_index):
        try:
            resp = httpx.post(
                f"http://{self.launcher.host}:{self.launcher.port}/api/jarvis/chat", 
                json={"message": task}, 
                timeout=30
            )
            resp_data = resp.json()
            self.root.after(0, self._resolve_main_task_response, resp_data, thinking_index, task)
        except Exception as e:
            self.root.after(0, self._resolve_main_task_error, str(e), thinking_index, task)

    def _resolve_main_task_response(self, resp_data, thinking_index, task):
        try:
            self.chat_history_viewer.config(state=tk.NORMAL)
            self.chat_history_viewer.delete(thinking_index, tk.END)
            self.chat_history_viewer.config(state=tk.DISABLED)
        except Exception:
            pass
        
        if "response" in resp_data:
            reply = resp_data["response"]
        elif "result" in resp_data:
            reply = resp_data["result"]
        elif "success" in resp_data:
            status_txt = "BAŞARILI" if resp_data["success"] else "BAŞARISIZ"
            reply = f"Görev Durumu: {status_txt}\nGörev ID: {resp_data.get('task_id', 'N/A')}\nÇalışma Modu: {resp_data.get('provider_mode', 'hybrid')}\n"
            if resp_data.get("created_files"):
                reply += f"Oluşturulan Dosyalar:\n" + "\n".join(f"- {f}" for f in resp_data["created_files"])
            else:
                reply += "Yeni dosya oluşturulmadı."
        else:
            reply = json.dumps(resp_data, indent=2, ensure_ascii=False)
            
        self.add_main_chat_message("jarvis", reply)
        self.append_log(f"[SUCCESS] Görev tamamlandı: {task}")
        
        # Trigger Jarvis to speak the reply if possible
        if hasattr(self, "voice_streamer") and hasattr(self.voice_streamer, "tts"):
            async def _speak():
                try:
                    async for chunk in self.voice_streamer.tts.stream_speak(reply):
                        if chunk and chunk != b"[SIMULATION]":
                            await self.voice_streamer.voice_client.play_audio_chunk(chunk)
                except Exception as e:
                    self.append_log(f"[WARNING] Ses sentezi hatası: {e}")
            
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_speak())
            except RuntimeError:
                threading.Thread(target=lambda: asyncio.run(_speak()), daemon=True).start()

    def _resolve_main_task_error(self, err_msg, thinking_index, task):
        try:
            self.chat_history_viewer.config(state=tk.NORMAL)
            self.chat_history_viewer.delete(thinking_index, tk.END)
            self.chat_history_viewer.config(state=tk.DISABLED)
        except Exception:
            pass
        
        self.add_main_chat_message("system", f"Görev iletimi başarısız: {err_msg}")
        self.append_log(f"[ERROR] Görev iletimi başarısız: {err_msg}")

    def show_context_menu(self, event):
        widget = event.widget
        try:
            widget.selection_get()
            self.context_menu.entryconfigure(0, state=tk.NORMAL)
        except tk.TclError:
            self.context_menu.entryconfigure(0, state=tk.DISABLED)
            
        self._last_focused_text_widget = widget
        self.context_menu.post(event.x_root, event.y_root)

    def copy_selected_text(self):
        if hasattr(self, "_last_focused_text_widget"):
            try:
                selected_text = self._last_focused_text_widget.selection_get()
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
                self.append_log("[INFO] Seçilen metin panoya kopyalandı.")
            except tk.TclError:
                pass

    def on_entry_focus_in(self, event):
        if self.input_entry.get() == "Jarvis'e görev ver":
            self.input_entry.delete(0, tk.END)

    def on_entry_focus_out(self, event):
        if not self.input_entry.get():
            self.input_entry.insert(0, "Jarvis'e görev ver")

    # --- ANİMASYONLU SİNİR AĞI METOTLARI ---
    def setup_neural_network(self):
        # 3 Layers setup
        self.net_nodes = []
        self.net_connections = []
        self.net_particles = []
        
        # Position points configuration (Input: 3, Hidden: 4, Output: 4)
        layers = [3, 4, 4]
        spacing_x = 100
        start_x = 60
        
        for l_idx, count in enumerate(layers):
            layer_nodes = []
            spacing_y = 170 / (count + 1)
            x = start_x + l_idx * spacing_x
            
            for n_idx in range(count):
                y = spacing_y * (n_idx + 1) + 15
                node_id = self.net_canvas.create_oval(x-6, y-6, x+6, y+6, fill=self.theme["background"], outline=self.theme["primary"], width=2)
                # Save coordinate points
                node_data = {
                    "id": node_id, "x": x, "y": y, "base_x": x, "base_y": y, "layer": l_idx, "index": n_idx, 
                    "base_r": 6, "pulse_phase": random.uniform(0, math.pi * 2),
                    "role": f"Agent_{l_idx}_{n_idx}",
                    "status": "AKTİF" if random.choice([True, True, False]) else "BOŞTA",
                    "throughput": f"{random.randint(80, 99)}%"
                }
                layer_nodes.append(node_data)
                self.net_nodes.append(node_data)
            
        # Draw synapses (Connecting lines)
        for i in range(len(layers) - 1):
            curr_nodes = [n for n in self.net_nodes if n["layer"] == i]
            next_nodes = [n for n in self.net_nodes if n["layer"] == i + 1]
            
            for cn in curr_nodes:
                for nn in next_nodes:
                    line_id = self.net_canvas.create_line(cn["x"], cn["y"], nn["x"], nn["y"], fill=self.theme["border"], width=1)
                    # Lower line behind nodes
                    self.net_canvas.tag_lower(line_id)
                    self.net_connections.append({
                        "id": line_id, "start_node": cn, "end_node": nn
                    })
                    
        # Active hover data display inside neural network
        self.hover_rect = self.net_canvas.create_rectangle(0, 0, 0, 0, fill="#0d1527", outline=self.theme["primary"], width=1, state=tk.HIDDEN)
        self.hover_text = self.net_canvas.create_text(0, 0, text="", fill=self.theme["text"], font=("Segoe UI", 8), state=tk.HIDDEN, justify=tk.LEFT)
        self.hud_text = self.net_canvas.create_text(260, 25, text="AĞ VERİMİ: %98.4\nGECİKME: 32ms", fill=self.theme["primary"], font=("Segoe UI", 8, "bold"), justify=tk.RIGHT)
        
        self.net_canvas.bind("<Motion>", self.on_neural_net_hover)
        self.net_canvas.bind("<Leave>", self.on_neural_net_leave)

    def on_neural_net_hover(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y
        mx, my = event.x, event.y
        nearest_node = None
        min_dist = 15.0 # pixels threshold
        
        for node in self.net_nodes:
            dist = math.hypot(node["x"] - mx, node["y"] - my)
            if dist < min_dist:
                min_dist = dist
                nearest_node = node
                
        if nearest_node:
            self.hovered_node = nearest_node
            # Highlight node on hover
            self.net_canvas.itemconfig(nearest_node["id"], outline=self.theme["accent"], width=3)
            
            # Show hover details box
            info_txt = f"Ajan: {nearest_node['role']}\nDurum: {nearest_node['status']}\nVerim: {nearest_node['throughput']}"
            rx, ry = nearest_node["x"] + 15, nearest_node["y"] - 25
            
            # Adjust if box hits borders
            if rx > 250:
                rx = nearest_node["x"] - 130
                
            self.net_canvas.coords(self.hover_rect, rx, ry, rx + 115, ry + 48)
            self.net_canvas.coords(self.hover_text, rx + 8, ry + 24)
            self.net_canvas.itemconfig(self.hover_text, text=info_txt)
            
            self.net_canvas.itemconfig(self.hover_rect, state=tk.NORMAL)
            self.net_canvas.itemconfig(self.hover_text, state=tk.NORMAL)
            
            # Raise hover box on top
            self.net_canvas.tag_raise(self.hover_rect)
            self.net_canvas.tag_raise(self.hover_text)
        else:
            self.hovered_node = None
            # Restore all node styles
            for node in self.net_nodes:
                self.net_canvas.itemconfig(node["id"], outline=self.theme["primary"], width=2)
            self.net_canvas.itemconfig(self.hover_rect, state=tk.HIDDEN)
            self.net_canvas.itemconfig(self.hover_text, state=tk.HIDDEN)

    def on_neural_net_leave(self, event):
        self.mouse_x = None
        self.mouse_y = None
        self.hovered_node = None

    def on_fin_canvas_hover(self, event):
        self.fin_mouse_x = event.x
        self.fin_mouse_y = event.y

    def on_fin_canvas_leave(self, event):
        self.fin_mouse_x = None
        self.fin_mouse_y = None

    # --- ANİMASYONLU SES DALGASI METOTLARI ---
    def draw_voice_waveform(self):
        self.wave_canvas.delete("wave")
        width = self.wave_canvas.winfo_width() or 400
        height = self.wave_canvas.winfo_height() or 85
        mid_y = height / 2
        
        # Get dynamic volume peak from voice client streamer
        live_amp = 0.0
        if hasattr(self, "voice_streamer") and hasattr(self.voice_streamer, "voice_client"):
            live_amp = self.voice_streamer.voice_client.last_amplitude
            
        # Organic wave amplitude with live volume scaling when active
        if self.voice_active:
            # Map [0, 1.0] live amplitude to [5, 40] height peak amplitude
            max_amp = 5.0 + (live_amp * 90.0)
            if max_amp > 42.0: max_amp = 42.0
        else:
            max_amp = 2.0
        
        # Overlapping Sine wave paths (Cyan, Magenta, Gold/Amber)
        points_cyan = []
        points_mag = []
        points_gold = []
        
        for x in range(0, width + 5, 5):
            rad = (x / width) * math.pi * 3
            envelope = math.sin((x / width) * math.pi) # Keeps the ends perfectly anchored at 0 amplitude
            
            # Wave 1 (Cyan): Multi-sine summation
            y_c = mid_y + max_amp * envelope * (math.sin(rad + self.wave_phase) + 0.35 * math.sin(2.3 * rad - 1.5 * self.wave_phase) + 0.15 * math.sin(5.7 * rad))
            points_cyan.extend([x, y_c])
            
            # Wave 2 (Magenta): Shifted multi-sine summation
            y_m = mid_y + (max_amp * 0.7) * envelope * (math.sin(rad * 1.5 - self.wave_phase * 1.2) + 0.35 * math.sin(3.1 * rad + self.wave_phase) + 0.2 * math.sin(4.5 * rad))
            points_mag.extend([x, y_m])

            # Wave 3 (Gold/Amber): Slow waving third background layer
            y_g = mid_y + (max_amp * 0.45) * envelope * (math.sin(rad * 0.8 + self.wave_phase * 0.7) + 0.25 * math.sin(1.7 * rad - self.wave_phase) + 0.1 * math.sin(3.2 * rad))
            points_gold.extend([x, y_g])
            
        if len(points_gold) >= 4:
            self.wave_canvas.create_line(points_gold, fill="#f59e0b", width=1, tags="wave", smooth=True)
        if len(points_cyan) >= 4:
            self.wave_canvas.create_line(points_cyan, fill=self.theme["primary"], width=2, tags="wave", smooth=True)
        if len(points_mag) >= 4:
            self.wave_canvas.create_line(points_mag, fill=self.theme["accent"], width=1, tags="wave", smooth=True)

    # --- ANİMASYONLU ALAN GRAFİKLERİ METOTLARI ---
    def draw_financial_chart(self):
        self.fin_canvas.delete("chart")
        width = self.fin_canvas.winfo_width() or 400
        height = self.fin_canvas.winfo_height() or 85
        
        # Border pad margins
        pad_x = 10
        pad_y = 10
        graph_w = width - (pad_x * 2)
        graph_h = height - (pad_y * 2)
        
        # Sample points wiggled slightly over time
        seed_points = [0.15, 0.35, 0.20, 0.45, 0.30, 0.60, 0.50, 0.75, 0.65, 0.85]
        
        coords = []
        for i, val in enumerate(seed_points):
            x = pad_x + (i / (len(seed_points) - 1)) * graph_w
            # Dynamic wiggle
            wiggle = math.sin(self.chart_step * 0.15 + i) * 0.03
            y = height - pad_y - (val + wiggle) * graph_h
            coords.append((x, y))
            
        # Draw area polygon filling downwards
        poly_points = [pad_x, height - pad_y]
        for pt in coords:
            poly_points.extend(pt)
        poly_points.extend([width - pad_x, height - pad_y])
        
        # Draw translucent gradient feeling filled polygon
        self.fin_canvas.create_polygon(poly_points, fill="#0f293b", outline="", tags="chart")
        
        # Draw the sharp neon line on top
        line_points = []
        for pt in coords:
            line_points.extend(pt)
        self.fin_canvas.create_line(line_points, fill=self.theme["success"], width=2, tags="chart", smooth=True)
        
        # Draw pulsing glowing circle at the end point
        end_x, end_y = coords[-1]
        pulse_r = 4 + 2 * math.sin(self.chart_step * 0.2)
        self.fin_canvas.create_oval(end_x - pulse_r, end_y - pulse_r, end_x + pulse_r, end_y + pulse_r, fill=self.theme["success"], width=0, tags="chart")

        # Dynamic coordinate hover tooltips
        fmx = getattr(self, "fin_mouse_x", None)
        fmy = getattr(self, "fin_mouse_y", None)
        if fmx is not None and fmy is not None:
            # Find the nearest index horizontally
            nearest_idx = 0
            min_dist = 99999.0
            for idx, pt in enumerate(coords):
                dist = abs(pt[0] - fmx)
                if dist < min_dist:
                    min_dist = dist
                    nearest_idx = idx
            
            if min_dist < 40:
                px, py = coords[nearest_idx]
                # Draw vertical dashed alignment guideline
                self.fin_canvas.create_line(px, pad_y, px, height - pad_y, fill=self.theme["border"], dash=(4, 2), tags="chart")
                # Draw pulsing highlight circle at the line node
                self.fin_canvas.create_oval(px - 6, py - 6, px + 6, py + 6, fill="", outline=self.theme["success"], width=2, tags="chart")
                self.fin_canvas.create_oval(px - 3, py - 3, px + 3, py + 3, fill=self.theme["success"], width=0, tags="chart")
                
                # Render sleek details tooltip card
                val = seed_points[nearest_idx]
                info_text = f"Zaman: T-{9-nearest_idx}\nROI: %{val*100:.1f}"
                box_w, box_h = 100, 36
                box_x = px + 10
                box_y = py - 40
                
                # Keep box within canvas bounds
                if box_x + box_w > width:
                    box_x = px - box_w - 10
                if box_y < 2:
                    box_y = py + 10
                    
                self.fin_canvas.create_rectangle(box_x, box_y, box_x + box_w, box_y + box_h, fill="#0d1527", outline=self.theme["success"], width=1, tags="chart")
                self.fin_canvas.create_text(box_x + 8, box_y + 18, text=info_text, fill=self.theme["text"], font=("Segoe UI", 8, "bold"), justify=tk.LEFT, anchor="w", tags="chart")

    def setup_mini_activity_graph(self):
        # A tiny decorative neon wave drawn on the header of activities
        self.act_graph_canvas.delete("all")
        self.act_graph_canvas.create_line(
            [(5, 18), (25, 6), (45, 14), (65, 4), (85, 16), (105, 8), (115, 12)], 
            fill=self.theme["primary"], width=1.5, smooth=True
        )

    # --- CANLI TELEMETRİ / DEPARTMAN DETAY MODALI ---
    def open_department_telemetry(self, dept_code):
        # Prevent opening multiple modals
        if hasattr(self, "modal_window") and self.modal_window:
            try: self.modal_window.destroy()
            except Exception: pass
            
        self.modal_window = tw = tk.Toplevel(self.root)
        tw.wm_overrideredirect(True)
        
        # Center the modal relative to parent window
        px = self.root.winfo_x()
        py = self.root.winfo_y()
        pw = self.root.winfo_width()
        ph = self.root.winfo_height()
        
        mw, mh = 480, 520
        mx = px + (pw - mw) // 2
        my = py + (ph - mh) // 2
        tw.wm_geometry(f"{mw}x{mh}+{mx}+{my}")
        tw.configure(bg=self.theme["surface"], highlightthickness=1, highlightbackground=self.theme["border"])
        
        # Title bar
        m_title = tk.Frame(tw, bg=self.theme["surface"])
        m_title.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        title_map = {
            "zeze_prompt": "🧠 ZEZE_PROMPT CANLI METRİKLER",
            "zeze_guard": "🛡️ ZEZE_GUARD CANLI METRİKLER",
            "zeze_sec": "🛡️ ZEZE_SEC CANLI METRİKLER",
            "zeze_rnd": "⚛️ ZEZE_RND CANLI METRİKLER",
            "zeze_eng": "⚙️ ZEZE_ENG CANLI METRİKLER",
            "crypto_trading": "📈 ZEZE_TRADING CANLI METRİKLER",
            "media_factory": "🎬 ZEZE_MEDIA CANLI METRİKLER"
        }
        dept_color = self.dept_widgets[dept_code]["color"]
        
        tk.Label(
            m_title, text=title_map[dept_code], font=("Segoe UI", 11, "bold"), bg=self.theme["surface"], fg=dept_color
        ).pack(side=tk.LEFT)
        
        close_btn = tk.Button(
            m_title, text="✕", font=("Segoe UI", 10, "bold"), bg=self.theme["surface"], fg=self.theme["text_muted"],
            activebackground=self.theme["error"], activeforeground="#ffffff", relief="flat", bd=0, width=3,
            command=tw.destroy
        )
        close_btn.pack(side=tk.RIGHT)
        
        # Content frame
        m_content = tk.Frame(tw, bg=self.theme["background"])
        m_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Scrollable area inside modal for detailed agent listings
        lbl_stats_title = tk.Label(
            m_content, text="📈 PERFORMANS METRİKLERİ", font=("Segoe UI", 9, "bold"), bg=self.theme["background"], fg=self.theme["primary"]
        )
        lbl_stats_title.pack(anchor="w", padx=15, pady=(12, 6))
        
        # Metrics list
        metrics_box = tk.Frame(m_content, bg=self.theme["background"])
        metrics_box.pack(fill=tk.X, padx=15)
        
        self.modal_labels = {}
        metric_labels = [
            ("Uptime:", "uptime"),
            ("Toplam API Çağrısı:", "api_calls"),
            ("Başarı Oranı:", "success_rate"),
            ("Kuyruk Derinliği (RabbitMQ):", "queue_depth"),
            ("Aktif Ajan Sayısı:", "active_agents"),
            ("Broker Bağlantısı:", "rabbitmq_connection"),
            ("Sistem Yükü:", "workload")
        ]
        
        for text, key in metric_labels:
            row = tk.Frame(metrics_box, bg=self.theme["background"])
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=text, font=("Segoe UI", 9), bg=self.theme["background"], fg=self.theme["text_muted"]).pack(side=tk.LEFT)
            val_lbl = tk.Label(row, text="Yükleniyor...", font=("Segoe UI", 9, "bold"), bg=self.theme["background"], fg=self.theme["text"])
            val_lbl.pack(side=tk.RIGHT)
            self.modal_labels[key] = val_lbl
            
        # Warning notification view
        self.audit_issues_lbl = tk.Label(
            m_content, text="", font=("Segoe UI", 9, "italic"), bg=self.theme["background"], fg=self.theme["warning"], wraplength=440, justify="left"
        )
        self.audit_issues_lbl.pack(anchor="w", padx=15, pady=(8, 0))

        # Hardware Usage Bars
        lbl_hw_title = tk.Label(
            m_content, text="💻 TELEMETRİ / SİSTEM KAYNAKLARI", font=("Segoe UI", 9, "bold"), bg=self.theme["background"], fg=self.theme["primary"]
        )
        lbl_hw_title.pack(anchor="w", padx=15, pady=(15, 6))
        
        hw_box = tk.Frame(m_content, bg=self.theme["background"])
        hw_box.pack(fill=tk.X, padx=15)
        
        self.modal_hw_bars = {}
        for hw in ["CPU", "RAM", "GPU"]:
            row = tk.Frame(hw_box, bg=self.theme["background"])
            row.pack(fill=tk.X, pady=4)
            tk.Label(row, text=f"{hw}:", font=("Segoe UI", 9), bg=self.theme["background"], fg=self.theme["text_muted"], width=5).pack(side=tk.LEFT)
            
            # Progress bar canvas
            bar_c = tk.Canvas(row, height=8, bg=self.theme["border"], highlightthickness=0)
            bar_c.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
            fill_r = bar_c.create_rectangle(0, 0, 0, 8, fill=dept_color, width=0)
            
            val_lbl = tk.Label(row, text="0%", font=("Segoe UI", 9, "bold"), bg=self.theme["background"], fg=self.theme["text"])
            val_lbl.pack(side=tk.RIGHT)
            self.modal_hw_bars[hw] = (bar_c, fill_r, val_lbl)
            
        # Agent list
        lbl_ag_title = tk.Label(
            m_content, text="👥 AKTİF AJANLAR & PROFİL ÖZETLERİ", font=("Segoe UI", 9, "bold"), bg=m_content["bg"], fg=self.theme["primary"]
        )
        lbl_ag_title.pack(anchor="w", padx=15, pady=(15, 6))
        
        self.agents_frame = tk.Frame(m_content, bg=self.theme["background"])
        self.agents_frame.pack(fill=tk.BOTH, expand=True, padx=15)
        
        # Start modal live data fetching loop
        self.update_modal_telemetry(tw, dept_code)

    def update_modal_telemetry(self, window, dept_code):
        # Stop looping if modal is destroyed
        if not window.winfo_exists():
            return
            
        # Fetch status data from backend or local simulation
        data = None
        try:
            resp = httpx.get(f"http://{self.launcher.host}:{self.launcher.port}/api/departments/{dept_code}/status", timeout=1)
            if resp.status_code == 200:
                data = resp.json()
        except Exception:
            pass
            
        # Fallback simulation
        if not data:
            data = self.generate_simulated_telemetry(dept_code)
            
        # Update metrics label values
        self.modal_labels["uptime"].config(text=data["uptime"])
        self.modal_labels["api_calls"].config(text=f"{data['api_calls']:,}")
        self.modal_labels["success_rate"].config(text=data["success_rate"])
        self.modal_labels["queue_depth"].config(text=str(data["queue_depth"]))
        self.modal_labels["active_agents"].config(text=str(data["active_agents"]))
        
        # Update dynamic audit statuses
        audit_data = data.get("audit", {})
        conn_status = audit_data.get("rabbitmq_connection", "FALLBACK_ACTIVE")
        workload_status = audit_data.get("workload", "NORMAL")
        issues_list = audit_data.get("issues", [])
        
        # Color coding connection badge
        if conn_status == "CONNECTED":
            self.modal_labels["rabbitmq_connection"].config(text="CONNECTED (Aktif)", fg="#10b981") # Emerald Green
        elif conn_status == "FALLBACK_ACTIVE":
            self.modal_labels["rabbitmq_connection"].config(text="FALLBACK_ACTIVE (Yedek Mod)", fg="#f59e0b") # Amber/Orange
        else:
            self.modal_labels["rabbitmq_connection"].config(text=conn_status, fg="#ef4444") # Red
            
        # Color coding workload badge
        if workload_status == "CRITICAL":
            self.modal_labels["workload"].config(text="CRITICAL (Kritik)", fg="#ef4444")
        elif workload_status == "HIGH":
            self.modal_labels["workload"].config(text="HIGH (Yüksek)", fg="#f59e0b")
        else:
            self.modal_labels["workload"].config(text="NORMAL (Normal)", fg="#10b981")
            
        # Update warning text
        if issues_list:
            warn_text = "⚠️ KRİTİK UYARILAR:\n" + "\n".join(f"- {issue}" for issue in issues_list)
            self.audit_issues_lbl.config(text=warn_text, fg="#f59e0b")
        else:
            self.audit_issues_lbl.config(text="✔ Sistem durumu stabil. Aktif uyarı bulunmuyor.", fg="#10b981")

        # Update Hardware usage bars
        dept_color = self.dept_widgets[dept_code]["color"]
        for hw in ["CPU", "RAM", "GPU"]:
            usage_str = data["system_usage"][hw.lower()]
            val_pct = int(usage_str.split("%")[0]) if "%" in usage_str else random.randint(10, 40)
            
            bar_c, fill_r, val_lbl = self.modal_hw_bars[hw]
            width = bar_c.winfo_width() or 200
            bar_c.coords(fill_r, 0, 0, (val_pct / 100) * width, 8)
            val_lbl.config(text=usage_str)
            
        # Render active agents profiles list
        for child in self.agents_frame.winfo_children():
            child.destroy()
            
        for ag in data.get("agents_list", []):
            ag_row = tk.Frame(self.agents_frame, bg=self.theme["background"])
            ag_row.pack(fill=tk.X, pady=3)
            
            tk.Label(
                ag_row, text=f"• {ag['name']}", font=("Segoe UI", 9, "bold"), bg=self.theme["background"], fg=self.theme["text"]
            ).pack(side=tk.LEFT)
            tk.Label(
                ag_row, text=f"({ag['role']})", font=("Segoe UI", 8), bg=self.theme["background"], fg=self.theme["text_muted"]
            ).pack(side=tk.LEFT, padx=5)
            
            # Status badge
            st_color = self.theme["success"] if ag["status"] in ["Ready", "Active", "Monitoring", "Writing Code", "Deploying", "Running Tests"] else self.theme["warning"]
            tk.Label(
                ag_row, text=ag["status"], font=("Segoe UI", 8, "bold"), bg=self.theme["background"], fg=st_color
            ).pack(side=tk.RIGHT, padx=5)
            tk.Label(
                ag_row, text=f"{ag['tokens']:,} Tok", font=("Segoe UI", 8), bg=self.theme["background"], fg=self.theme["primary"]
            ).pack(side=tk.RIGHT)
            
            # 📊 Workload horizontal mini canvas bar next to agent's status
            workload_c = tk.Canvas(ag_row, width=40, height=6, bg=self.theme["border"], highlightthickness=0)
            workload_c.pack(side=tk.RIGHT, padx=8)
            status_lower = ag["status"].lower()
            if any(k in status_lower for k in ["ready", "active", "monitoring", "running", "writing"]):
                w_color = "#10b981" # Emerald Green
                fill_w = 40
            elif any(k in status_lower for k in ["busy", "deploying", "analyzing", "scanning", "optimizing", "testing"]):
                w_color = "#f59e0b" # Amber/Orange
                fill_w = 25
            else:
                w_color = "#ef4444" # Crimson Red
                fill_w = 10
            workload_c.create_rectangle(0, 0, fill_w, 6, fill=w_color, width=0)
            
        # Recursive loop call every 2.5s
        self.root.after(2500, lambda: self.update_modal_telemetry(window, dept_code))

    def generate_simulated_telemetry(self, dept_code):
        import random
        # Mapping realistic simulation metrics
        res = {
            "uptime": "99.9%",
            "api_calls": random.randint(10000, 20000),
            "success_rate": f"{random.uniform(99.0, 99.9):.2f}%",
            "queue_depth": random.randint(0, 4),
            "active_agents": 3,
            "system_usage": {
                "cpu": f"{random.randint(15, 60)}%",
                "ram": f"{random.randint(70, 190)} MB",
                "gpu": f"{random.randint(0, 40)}%"
            },
            "audit": {
                "rabbitmq_connection": "FALLBACK_ACTIVE",
                "config_status": "OK",
                "issues": ["RabbitMQ broker pasif, yerel fallback kuyrukları kullanılıyor."] if dept_code == "zeze_eng" else [],
                "workload": "NORMAL"
            },
            "agents_list": []
        }
        
        if dept_code == "zeze_prompt":
            res["agents_list"] = [
                {"name": "Prompt Architect", "role": "System Prompt Engineering", "status": "Ready", "tokens": random.randint(40000, 70000)},
                {"name": "Context Optimizer", "role": "RAG Prompt Refinement", "status": "Active", "tokens": random.randint(20000, 40000)}
            ]
        elif dept_code == "zeze_guard":
            res["agents_list"] = [
                {"name": "Budget Enforcement", "role": "Token Spend Limit", "status": "Monitoring", "tokens": random.randint(80000, 110000)},
                {"name": "Policy Engine", "role": "Compliance & DLP", "status": "Active", "tokens": random.randint(30000, 50000)}
            ]
        elif dept_code == "zeze_sec":
            res["agents_list"] = [
                {"name": "Vulnerability Scanner", "role": "Source Code Audit", "status": "Scanning", "tokens": random.randint(60000, 90000)},
                {"name": "Network Shield", "role": "WAF & API Guard", "status": "Monitoring", "tokens": random.randint(70000, 100000)}
            ]
        elif dept_code == "zeze_rnd":
            res["agents_list"] = [
                {"name": "Trend Scout", "role": "GitHub & arXiv Monitor", "status": "Scouting", "tokens": random.randint(10000, 20000)},
                {"name": "Sandbox Engineer", "role": "Package Benchmarking", "status": "Testing", "tokens": random.randint(5000, 15000)}
            ]
        elif dept_code == "zeze_eng":
            res["agents_list"] = [
                {"name": "Dev Lead", "role": "Code Synthesis & Refactor", "status": "Writing Code", "tokens": random.randint(100000, 160000)},
                {"name": "RabbitMQ Integrator", "role": "Message Broker Setup", "status": "Deploying", "tokens": random.randint(40000, 70000)}
            ]
        elif dept_code == "crypto_trading":
            res["agents_list"] = [
                {"name": "Market Scanner", "role": "Order Book Liquidity Monitor", "status": "Monitoring", "tokens": random.randint(150000, 220000)},
                {"name": "Risk Evaluator", "role": "Leverage & Margin Guard", "status": "Ready", "tokens": random.randint(80000, 110000)},
                {"name": "Execution Bot", "role": "Smart Order Routing", "status": "Idle", "tokens": random.randint(50000, 70000)}
            ]
        elif dept_code == "media_factory":
            res["agents_list"] = [
                {"name": "Content Generator", "role": "Video Synthesis & Rendering", "status": "Rendering", "tokens": random.randint(40000, 60000)},
                {"name": "Asset Pipeline", "role": "Post-processing & Metadata", "status": "Idle", "tokens": random.randint(10000, 15000)}
            ]
            
        return res

    # --- VOICE SETTINGS POPUP MODAL ---
    def open_voice_settings(self):
        if hasattr(self, "settings_window") and self.settings_window:
            try: self.settings_window.destroy()
            except Exception: pass
            
        self.settings_window = tw = tk.Toplevel(self.root)
        tw.wm_overrideredirect(True)
        
        # Center popup overlay
        px = self.root.winfo_x()
        py = self.root.winfo_y()
        pw = self.root.winfo_width()
        ph = self.root.winfo_height()
        
        mw, mh = 360, 280
        mx = px + (pw - mw) // 2
        my = py + (ph - mh) // 2
        tw.wm_geometry(f"{mw}x{mh}+{mx}+{my}")
        tw.configure(bg=self.theme["surface"], highlightthickness=1, highlightbackground=self.theme["border"])
        
        m_title = tk.Frame(tw, bg=self.theme["surface"])
        m_title.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        tk.Label(
            m_title, text="🎙️ SES VE SOHBET AYARLARI", font=("Segoe UI", 10, "bold"), bg=self.theme["surface"], fg=self.theme["primary"]
        ).pack(side=tk.LEFT)
        
        tk.Button(
            m_title, text="✕", font=("Segoe UI", 9, "bold"), bg=self.theme["surface"], fg=self.theme["text_muted"],
            activebackground=self.theme["error"], activeforeground="#ffffff", relief="flat", bd=0, width=3,
            command=tw.destroy
        )
        close_btn = m_title.winfo_children()[-1]
        close_btn.pack(side=tk.RIGHT)
        
        m_content = tk.Frame(tw, bg=self.theme["background"])
        m_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Config options sliders/toggles
        tk.Label(m_content, text="Mikrofon Hassasiyeti (Whisper):", font=("Segoe UI", 9), bg=m_content["bg"], fg=self.theme["text"]).pack(anchor="w", padx=15, pady=(12, 2))
        mic_scale = tk.Scale(m_content, from_=0, to=100, orient=tk.HORIZONTAL, bg=m_content["bg"], fg=self.theme["primary"], highlightthickness=0, troughcolor=self.theme["border"])
        mic_scale.set(75)
        mic_scale.pack(fill=tk.X, padx=15)
        
        tk.Label(m_content, text="Hoparlör Ses Düzeyi:", font=("Segoe UI", 9), bg=m_content["bg"], fg=self.theme["text"]).pack(anchor="w", padx=15, pady=(10, 2))
        spk_scale = tk.Scale(m_content, from_=0, to=100, orient=tk.HORIZONTAL, bg=m_content["bg"], fg=self.theme["primary"], highlightthickness=0, troughcolor=self.theme["border"])
        spk_scale.set(80)
        spk_scale.pack(fill=tk.X, padx=15)
        
        # TTS Engine speed selection option
        row_speed = tk.Frame(m_content, bg=m_content["bg"])
        row_speed.pack(fill=tk.X, padx=15, pady=(15, 10))
        tk.Label(row_speed, text="PlayHT TTS Ses Hızı:", font=("Segoe UI", 9), bg=row_speed["bg"], fg=self.theme["text"]).pack(side=tk.LEFT)
        
        speed_var = tk.StringVar(value="Normal (1.0x)")
        speed_opt = tk.OptionMenu(row_speed, speed_var, "Yavaş (0.8x)", "Normal (1.0x)", "Hızlı (1.25x)", "Ultra Hızlı (1.5x)")
        speed_opt.config(bg=self.theme["surface"], fg=self.theme["text"], relief="flat", highlightthickness=0)
        speed_opt["menu"].config(bg=self.theme["surface"], fg=self.theme["text"])
        speed_opt.pack(side=tk.RIGHT)
        
        save_btn = self.create_premium_button(
            m_content, text="AYARLARI KAYDET", command=lambda: [self.append_log("[INFO] Ses ayarları başarıyla güncellendi."), tw.destroy()],
            bg=self.theme["primary"], fg=self.theme["background"]
        )
        save_btn.pack(fill=tk.X, side=tk.BOTTOM, padx=15)

    def toggle_mic(self):
        if hasattr(self, "mic_toggle"):
            self.mic_toggle.toggle()

    def toggle_chat_drawer(self):
        self.toggle_drawer()
        if self.drawer_expanded:
            self.input_entry.focus_set()

    def on_mic_toggle(self, state):
        self.voice_active = state
        if self.voice_active:
            self.voice_status_lbl.config(text="DURUM: DİNLİYOR", fg=self.theme["primary"])
            self.append_log("[INFO] Canlı ses kanalı mikrofonu açıldı.")
            if hasattr(self, "voice_streamer"):
                self.voice_streamer.start_mic_stream()
        else:
            self.voice_status_lbl.config(text="DURUM: AKTİF", fg=self.theme["success"])
            self.append_log("[INFO] Canlı ses kanalı mikrofonu kapatıldı.")
            if hasattr(self, "voice_streamer"):
                self.voice_streamer.stop_mic_stream()

    # --- ANİMASYON EVENT LOOP (Thread-Safe trigger) ---
    def animate_loop(self):
        try:
            # 1. Sine wave equalizer phase shift
            self.wave_phase += 0.12
            self.draw_voice_waveform()
            
            # 2. Area line charts shift step
            self.chart_step += 1
            self.draw_financial_chart()
            
            # 3. Progress track bar horizontal scroll
            width = self.progress_canvas.winfo_width() or 300
            self.progress_x += self.progress_dir * 3
            if self.progress_x > width - 60:
                self.progress_dir = -1
            elif self.progress_x < 0:
                self.progress_dir = 1
            self.progress_canvas.coords(self.progress_bar, self.progress_x, 0, self.progress_x + 60, 3)
            
            # 4. Neural Network particles motion & nodes pulsing
            self.animate_neural_network()
            
            # Call loop again in 33ms (Targeting stable 30fps)
            self.root.after(33, self.animate_loop)
        except Exception:
            pass

    def animate_neural_network(self):
        # Delete previous glows
        self.net_canvas.delete("glow")
        
        # 1. Update Node positions with gravitational mouse warping
        for node in self.net_nodes:
            if getattr(self, "mouse_x", None) is not None and getattr(self, "mouse_y", None) is not None:
                dx = self.mouse_x - node["base_x"]
                dy = self.mouse_y - node["base_y"]
                dist = math.hypot(dx, dy)
                if dist < 85:
                    warp_factor = (85 - dist) / 85
                    target_x = node["base_x"] + dx * warp_factor * 0.25
                    target_y = node["base_y"] + dy * warp_factor * 0.25
                else:
                    target_x = node["base_x"]
                    target_y = node["base_y"]
            else:
                target_x = node["base_x"]
                target_y = node["base_y"]
            
            # Smooth elastic interpolation
            node["x"] += (target_x - node["x"]) * 0.15
            node["y"] += (target_y - node["y"]) * 0.15
            
            # Pulse ovals
            node["pulse_phase"] += 0.05
            offset = math.sin(node["pulse_phase"]) * 1.5
            r = node["base_r"] + offset
            self.net_canvas.coords(node["id"], node["x"] - r, node["y"] - r, node["x"] + r, node["y"] + r)

        # Draw double glowing rings around hovered_node
        if getattr(self, "hovered_node", None) is not None:
            if not hasattr(self, "glow_phase"):
                self.glow_phase = 0.0
            self.glow_phase += 0.15
            
            hx = self.hovered_node["x"]
            hy = self.hovered_node["y"]
            hr = self.hovered_node["base_r"]
            
            glow_expand1 = hr * 1.5 + math.sin(self.glow_phase) * 3
            glow_expand2 = hr * 3.0 + math.cos(self.glow_phase) * 5
            
            # Outer ring: pink/magenta neon glow
            self.net_canvas.create_oval(
                hx - glow_expand2, hy - glow_expand2, 
                hx + glow_expand2, hy + glow_expand2, 
                outline="#ff007f", width=1, tags="glow"
            )
            # Inner ring: turquoise/cyan neon glow
            self.net_canvas.create_oval(
                hx - glow_expand1, hy - glow_expand1, 
                hx + glow_expand1, hy + glow_expand1, 
                outline="#00ffcc", width=2, tags="glow"
            )
            self.net_canvas.tag_lower("glow")

        # 2. Update Synapse line coordinates
        for conn in self.net_connections:
            self.net_canvas.coords(
                conn["id"], 
                conn["start_node"]["x"], conn["start_node"]["y"], 
                conn["end_node"]["x"], conn["end_node"]["y"]
            )

        # Update dynamic HUD text on canvas
        if self.chart_step % 15 == 0:
            latency = random.randint(24, 38)
            throughput = random.uniform(97.8, 99.4)
            self.net_canvas.itemconfig(self.hud_text, text=f"AĞ VERİMİ: %{throughput:.1f}\nGECİKME: {latency}ms")

        # 3. Emit signal particles along connected lines periodically
        if self.chart_step % 8 == 0 and len(self.net_connections) > 0:
            conn = random.choice(self.net_connections)
            color = self.theme["primary"] if random.choice([True, False]) else self.theme["accent"]
            p_id = self.net_canvas.create_oval(
                conn["start_node"]["x"] - 2.5, conn["start_node"]["y"] - 2.5, 
                conn["start_node"]["x"] + 2.5, conn["start_node"]["y"] + 2.5, 
                fill=color, width=0
            )
            self.net_particles.append({
                "id": p_id, 
                "start_node": conn["start_node"], 
                "end_node": conn["end_node"], 
                "progress": 0.0
            })
            
        # 4. Update active particle positions
        active_p = []
        for p in self.net_particles:
            p["progress"] += 0.045
            if p["progress"] >= 1.0:
                self.net_canvas.delete(p["id"])
            else:
                x = p["start_node"]["x"] + (p["end_node"]["x"] - p["start_node"]["x"]) * p["progress"]
                y = p["start_node"]["y"] + (p["end_node"]["y"] - p["start_node"]["y"]) * p["progress"]
                self.net_canvas.coords(p["id"], x - 2.5, y - 2.5, x + 2.5, y + 2.5)
                active_p.append(p)
        self.net_particles = active_p
        
        # 5. Pulse circles inside department buttons (Centered at (18, 26) on the compact canvas)
        for code, dept in self.dept_widgets.items():
            dept["pulse_val"] += dept["pulse_dir"] * 0.1
            if dept["pulse_val"] > 1.0:
                dept["pulse_dir"] = -1
            elif dept["pulse_val"] < 0.1:
                dept["pulse_dir"] = 1
                
            opacity_r = 2.5 + dept["pulse_val"] * 1.5
            dept["canvas"].coords(dept["dot"], 18 - opacity_r, 26 - opacity_r, 18 + opacity_r, 26 + opacity_r)

    # --- TELEMETRİ / BACKEND HEALTH GÜNCELLEMELERİ ---
    def update_telemetry_loop(self):
        try:
            base = 142.5
            offset = random.uniform(-1.5, 1.5)
            self.memory_lbl.config(text=f"Memory: {base + offset:.1f} MB / 512 MB")
            
            # Fetch backend status to double check online state
            self.check_status()
            
            # Dynamically update department cards from backend
            self.update_dashboard_departments()
        except Exception:
            pass
        self.root.after(3000, self.update_telemetry_loop)

    def update_dashboard_departments(self):
        def worker():
            updates = {}
            for code in list(self.dept_widgets.keys()):
                try:
                    resp = httpx.get(f"http://{self.launcher.host}:{self.launcher.port}/api/departments/{code}/status", timeout=0.8)
                    if resp.status_code == 200:
                        data = resp.json()
                        status_val = data.get("status", "AKTİF")
                        uptime = data.get("uptime", "99.9%")
                        active_agents = data.get("active_agents", 0)
                        
                        orig_color = self.dept_widgets[code]["color"]
                        
                        if status_val in ["MEŞGÜL", "MEŞGUL"]:
                            status_text = f"MEŞGUL | {active_agents} Ajan Aktif"
                            color = "#f59e0b"  # Amber/Orange for Busy
                        elif status_val == "TARANIYOR":
                            status_text = f"TARANIYOR | {active_agents} Ajan"
                            color = "#eab308"  # Yellow for Scanning
                        elif status_val == "AKTİF":
                            status_text = f"AKTİF | {uptime} Optimize"
                            color = "#10b981"  # Emerald Green for Active
                        else:
                            status_text = status_val
                            color = orig_color
                            
                        updates[code] = {
                            "text": status_text,
                            "color": color,
                            "online": True
                        }
                except Exception:
                    updates[code] = {
                        "text": "ÇEVRİMDIŞI | Bağlantı Yok",
                        "color": "#ef4444",  # Red for Offline
                        "online": False
                    }
            
            try:
                if self.root.winfo_exists():
                    self.root.after(0, lambda: self.apply_department_updates(updates))
            except Exception:
                pass
                
        threading.Thread(target=worker, daemon=True).start()

    def apply_department_updates(self, updates):
        for code, info in updates.items():
            if code in self.dept_widgets:
                widget_info = self.dept_widgets[code]
                lbl = widget_info["lbl_status"]
                lbl.config(text=info["text"], fg=info["color"])
                
                dot_color = info["color"] if not info["online"] else widget_info["color"]
                widget_info["canvas"].itemconfig(widget_info["dot"], fill=dot_color)
    def check_status(self):
        def worker():
            try:
                status = self.launcher.health_check()
                if self.root.winfo_exists():
                    self.root.after(0, lambda: self.apply_status_update(status))
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()

    def apply_status_update(self, status):
        try:
            if status["status"] == "online":
                data = status.get("data", {})
                self.badge_canvas.itemconfig(self.status_circle, fill=self.theme["success"])
                self.status_text_lbl.config(text="Online", fg=self.theme["success"])
                
                ai_mode = data.get("ai_mode", "hybrid_deepseek_hermes")
                self.ai_mode_lbl.config(text=f"AI Mode: {ai_mode}", fg=self.theme["primary"])
                
                # Bind dynamic API Balance
                balance = data.get("openrouter_balance", "$1,450.00")
                sub = data.get("subscription", "Standart 2TB")
                self.kpi_lbl.config(text=f"API BAKİYESİ: {balance} (OPENROUTER)  |  Abonelik: {sub}")
            else:
                self.badge_canvas.itemconfig(self.status_circle, fill=self.theme["error"])
                self.status_text_lbl.config(text="Offline", fg=self.theme["text_muted"])
                self.ai_mode_lbl.config(text="AI Mode: offline", fg=self.theme["text_muted"])
                self.kpi_lbl.config(text="API BAKİYESİ: Çevrimdışı (OPENROUTER)  |  Abonelik: Çevrimdışı")
        except Exception:
            pass

    def start_backend(self):
        res = self.launcher.start_backend()
        messagebox.showinfo("Result", res["message"])
        self.check_status()

    def stop_backend(self):
        res = self.launcher.stop_backend()
        messagebox.showinfo("Result", res["message"])
        self.check_status()

    def open_docs(self):
        self.launcher.open_browser_dashboard()
        
    def open_matrix(self):
        webbrowser.open("http://localhost:3000")

    def add_chat_message(self, sender, text):
        self.response_viewer.config(state=tk.NORMAL)
        if sender == "user":
            self.response_viewer.insert(tk.END, "👤 KULLANICI\n", "user_header")
            self.response_viewer.insert(tk.END, f"  {text}   ⚡  \n\n", "user_bubble")
        elif sender == "jarvis":
            self.response_viewer.insert(tk.END, "⚡ JARVIS\n", "jarvis_header")
            self.response_viewer.insert(tk.END, f"  {text}  \n\n", "jarvis_bubble")
        else: # system
            self.response_viewer.insert(tk.END, f"⚠️ {text}\n\n", "system_alert")
        self.response_viewer.see(tk.END)
        self.response_viewer.config(state=tk.DISABLED)

    def send_voice_text_task(self, task):
        if not task:
            return
            
        # Show "thinking..." status bubbles in Chat
        self.response_viewer.config(state=tk.NORMAL)
        thinking_index = self.response_viewer.index(tk.END + "-1c")
        self.response_viewer.insert(tk.END, "⚡ JARVIS: Düşünüyor...\n", "jarvis_header")
        self.response_viewer.insert(tk.END, " • • • \n\n", "jarvis_bubble")
        self.response_viewer.see(tk.END)
        self.response_viewer.config(state=tk.DISABLED)
        
        # Start a background thread to send the HTTP post request asynchronously
        threading.Thread(target=self._async_send_task, args=(task, thinking_index), daemon=True).start()

    def send_task(self, event=None):
        task = self.input_entry.get()
        if not task or task == "Jarvis'e görev ver":
            messagebox.showwarning("Uyarı", "Lütfen geçerli bir görev girin.")
            return
            
        self.add_chat_message("user", task)
        self.input_entry.delete(0, tk.END)
        
        # Show "thinking..." status bubbles in Chat
        self.response_viewer.config(state=tk.NORMAL)
        thinking_index = self.response_viewer.index(tk.END + "-1c")
        self.response_viewer.insert(tk.END, "⚡ JARVIS: Düşünüyor...\n", "jarvis_header")
        self.response_viewer.insert(tk.END, " • • • \n\n", "jarvis_bubble")
        self.response_viewer.see(tk.END)
        self.response_viewer.config(state=tk.DISABLED)
        
        # Start a background thread to send the HTTP post request asynchronously (no UI lockup!)
        threading.Thread(target=self._async_send_task, args=(task, thinking_index), daemon=True).start()

    def _async_send_task(self, task, thinking_index):
        try:
            resp = httpx.post(
                f"http://{self.launcher.host}:{self.launcher.port}/api/jarvis/chat", 
                json={"message": task}, 
                timeout=10
            )
            resp_data = resp.json()
            self.root.after(0, self._resolve_task_response, resp_data, thinking_index, task)
        except Exception as e:
            self.root.after(0, self._resolve_task_error, str(e), thinking_index, task)

    def _resolve_task_response(self, resp_data, thinking_index, task):
        # Remove thinking/waiting lines
        try:
            self.response_viewer.config(state=tk.NORMAL)
            self.response_viewer.delete(thinking_index, tk.END)
            self.response_viewer.config(state=tk.DISABLED)
        except Exception:
            pass
        
        if "response" in resp_data:
            reply = resp_data["response"]
        elif "result" in resp_data:
            reply = resp_data["result"]
        elif "success" in resp_data:
            status_txt = "BAŞARILI" if resp_data["success"] else "BAŞARISIZ"
            reply = f"Görev Durumu: {status_txt}\nGörev ID: {resp_data.get('task_id', 'N/A')}\nÇalışma Modu: {resp_data.get('provider_mode', 'hybrid')}\n"
            if resp_data.get("created_files"):
                reply += f"Oluşturulan Dosyalar:\n" + "\n".join(f"- {f}" for f in resp_data["created_files"])
            else:
                reply += "Yeni dosya oluşturulmadı."
        else:
            reply = json.dumps(resp_data, indent=2, ensure_ascii=False)
            
        self.add_chat_message("jarvis", reply)
        self.append_log(f"[SUCCESS] Görev tamamlandı: {task}")
        
        # Trigger Jarvis to speak the reply
        if hasattr(self, "voice_streamer") and hasattr(self.voice_streamer, "tts"):
            async def _speak():
                try:
                    async for chunk in self.voice_streamer.tts.stream_speak(reply):
                        if chunk and chunk != b"[SIMULATION]":
                            await self.voice_streamer.voice_client.play_audio_chunk(chunk)
                except Exception as e:
                    self.append_log(f"[WARNING] Ses sentezi hatası: {e}")
            
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_speak())
            except RuntimeError:
                threading.Thread(target=lambda: asyncio.run(_speak()), daemon=True).start()
    def _resolve_task_error(self, err_msg, thinking_index, task):
        # Remove thinking/waiting lines
        try:
            self.response_viewer.config(state=tk.NORMAL)
            self.response_viewer.delete(thinking_index, tk.END)
            self.response_viewer.config(state=tk.DISABLED)
        except Exception:
            pass
        
        self.add_chat_message("system", f"Görev iletimi başarısız: {err_msg}")
        self.append_log(f"[ERROR] Görev iletimi başarısız: {err_msg}")

    # --- SSE LOG AKIŞINI YAKALAMA VE DİNAMİK DEPARTMAN GÜNCELLEMELERİ ---
    def on_log_received(self, log_msg):
        self.log_queue.put(log_msg)

    def process_queue_loop(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.append_log(msg)
        except Empty:
            pass
        self.root.after(100, self.process_queue_loop)

    def append_log(self, text_line):
        try:
            self.activity_log_viewer.config(state=tk.NORMAL)
            
            start_pos = self.activity_log_viewer.index(tk.END + "-1c")
            self.activity_log_viewer.insert(tk.END, text_line + "\n")
            end_pos = self.activity_log_viewer.index(tk.END + "-1c")
            
            # Check keywords to dynamically color badge lines by department
            text_upper = text_line.upper()
            tag_name = None
            if "ZEZE_PROMPT" in text_upper:
                tag_name = "zeze_prompt"
            elif "ZEZE_GUARD" in text_upper:
                tag_name = "zeze_guard"
            elif "ZEZE_SEC" in text_upper:
                tag_name = "zeze_sec"
            elif "ZEZE_RND" in text_upper:
                tag_name = "zeze_rnd"
            elif "ZEZE_ENG" in text_upper:
                tag_name = "zeze_eng"
            elif "CEO" in text_upper or "GÖLGE" in text_upper:
                tag_name = "ceo"
                
            if tag_name:
                self.activity_log_viewer.tag_add(tag_name, start_pos, end_pos)
                
            # Scroll keeping end in view
            content = self.activity_log_viewer.get("1.0", tk.END)
            if len(content.splitlines()) > 500:
                self.activity_log_viewer.delete("1.0", "50.0")
            self.activity_log_viewer.see(tk.END)
            self.activity_log_viewer.config(state=tk.DISABLED)
        except Exception:
            pass

    # --- TITLE BAR DRAG VE WINDOW OPERATIONS ---
    def on_drag_start(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def on_drag_motion(self, event):
        if self._is_maximized:
            return
        x = self.root.winfo_pointerx() - self._drag_start_x
        y = self.root.winfo_pointery() - self._drag_start_y
        self.root.geometry(f"+{x}+{y}")

    def minimize_window(self):
        try:
            self.root.overrideredirect(False)
            self.root.iconify()
            
            def restore_override(event):
                try: self.root.overrideredirect(True)
                except Exception: pass
                self.root.unbind("<Map>")
            self.root.bind("<Map>", restore_override)
        except Exception:
            pass

    def toggle_maximize(self):
        try:
            if self._is_maximized:
                self.root.geometry(self._prev_geometry)
                self._is_maximized = False
                self.max_btn.config(text="⬜")
            else:
                self._prev_geometry = self.root.geometry()
                screen_w = self.root.winfo_screenwidth()
                screen_h = self.root.winfo_screenheight()
                self.root.geometry(f"{screen_w}x{screen_h - 40}+0+0")
                self._is_maximized = True
                self.max_btn.config(text="❐")
        except Exception:
            pass

    def close_window(self):
        self.on_closing()

    def draw_header_gradient(self, event=None):
        try:
            width = self.gradient_canvas.winfo_width()
            if width <= 1:
                width = 1150
            self.gradient_canvas.delete("gradient")
            
            c1 = self.theme["accent"]
            c2 = self.theme["primary"]
            
            r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
            r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
            
            for i in range(width):
                ratio = i / width
                r = int(r1 + (r2 - r1) * ratio)
                g = int(g1 + (g2 - g1) * ratio)
                b = int(b1 + (b2 - b1) * ratio)
                color = f"#{r:02x}{g:02x}{b:02x}"
                self.gradient_canvas.create_line(i, 0, i, 4, fill=color, tags="gradient")
        except Exception:
            pass

    def on_closing(self):
        if hasattr(self, 'sse_client'):
            self.sse_client.stop()
        self.root.destroy()

def main():
    try:
        root = tk.Tk()
        app = JarvisDesktopApp(root)
        root.mainloop()
    except Exception as e:
        print("Failed to start GUI:", e)

if __name__ == "__main__":
    main()
