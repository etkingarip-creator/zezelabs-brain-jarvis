import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
import httpx
import webbrowser
from queue import Queue, Empty
import random
import json

from desktop.backend_launcher import BackendLauncher
from desktop.theme.colors import get_theme
from desktop.sse_client import SSELogClient

class JarvisDesktopApp:
    def __init__(self, root):
        self.root = root
        self.theme = get_theme()
        
        # Window configuration (Premium Borderless)
        self.root.overrideredirect(True)
        self.root.minsize(900, 650)
        self.root.configure(bg=self.theme["background"])
        
        # Center the window on start
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        width = 950
        height = 680
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
        
        # Create UI
        self.setup_ui()
        
        # Start background SSE log client
        backend_url = f"http://{self.launcher.host}:{self.launcher.port}/api/runtime/streamlogs"
        self.sse_client = SSELogClient(url=backend_url)
        self.sse_client.start(self.on_log_received)
        
        # Start periodic UI update loops
        self.check_status()
        self.process_queue_loop()
        self.animate_progress()
        self.update_memory_usage()
        
        # Clean shutdown handling
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        # --- CUSTOM TITLE BAR ---
        self.title_bar = tk.Frame(
            self.root, 
            bg=self.theme["surface"], 
            height=36,
            highlightthickness=0
        )
        self.title_bar.pack(fill=tk.X, side=tk.TOP)
        self.title_bar.pack_propagate(False)
        
        # Drag hooks
        self.title_bar.bind("<Button-1>", self.on_drag_start)
        self.title_bar.bind("<B1-Motion>", self.on_drag_motion)
        
        title_lbl = tk.Label(
            self.title_bar,
            text="⚡ JARVIS OPERATING SYSTEM CORE",
            font=("Segoe UI", 10, "bold"),
            bg=self.theme["surface"],
            fg=self.theme["primary"]
        )
        title_lbl.pack(side=tk.LEFT, padx=15)
        title_lbl.bind("<Button-1>", self.on_drag_start)
        title_lbl.bind("<B1-Motion>", self.on_drag_motion)
        
        # Title bar controls on the right
        controls_frame = tk.Frame(self.title_bar, bg=self.theme["surface"])
        controls_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.min_btn = tk.Button(
            controls_frame,
            text="—",
            bg=self.theme["surface"],
            fg=self.theme["text_muted"],
            activebackground=self.theme["border"],
            activeforeground=self.theme["text"],
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            width=4,
            height=2,
            command=self.minimize_window
        )
        self.min_btn.pack(side=tk.LEFT, fill=tk.Y)
        
        self.max_btn = tk.Button(
            controls_frame,
            text="⬜",
            bg=self.theme["surface"],
            fg=self.theme["text_muted"],
            activebackground=self.theme["border"],
            activeforeground=self.theme["text"],
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            width=4,
            height=2,
            command=self.toggle_maximize
        )
        self.max_btn.pack(side=tk.LEFT, fill=tk.Y)
        
        self.close_btn = tk.Button(
            controls_frame,
            text="✕",
            bg=self.theme["surface"],
            fg=self.theme["text_muted"],
            activebackground=self.theme["error"],
            activeforeground="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            width=4,
            height=2,
            command=self.close_window
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
        self.gradient_canvas = tk.Canvas(
            self.root, 
            height=4, 
            bg=self.theme["background"], 
            highlightthickness=0
        )
        self.gradient_canvas.pack(fill=tk.X, side=tk.TOP)
        self.gradient_canvas.bind("<Configure>", self.draw_header_gradient)
        
        # --- MAIN BODY CONTAINER ---
        main_container = tk.Frame(self.root, bg=self.theme["background"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(10, 15))
        
        main_container.columnconfigure(0, weight=4) # Left Column (Controls / Status)
        main_container.columnconfigure(1, weight=6) # Right Column (Logs / Response)
        main_container.rowconfigure(0, weight=1)
        
        # --- LEFT COLUMN ---
        left_frame = tk.Frame(
            main_container, 
            bg=self.theme["surface"], 
            bd=0, 
            highlightthickness=1, 
            highlightbackground=self.theme["border"]
        )
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)
        
        status_header = tk.Label(
            left_frame, 
            text="SYSTEM CORE STATUS", 
            font=("Segoe UI", 12, "bold"), 
            bg=self.theme["surface"], 
            fg=self.theme["primary"]
        )
        status_header.pack(pady=(15, 8), anchor="w", padx=15)
        
        # Status details card
        status_card = tk.Frame(
            left_frame, 
            bg=self.theme["background"],
            highlightthickness=1,
            highlightbackground=self.theme["border"]
        )
        status_card.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        # 1. Gateway Status
        row_gw = tk.Frame(status_card, bg=self.theme["background"])
        row_gw.pack(fill=tk.X, padx=12, pady=6)
        
        lbl_health = tk.Label(
            row_gw, 
            text="Core Gateway:", 
            font=("Segoe UI", 9, "bold"), 
            bg=self.theme["background"], 
            fg=self.theme["text"]
        )
        lbl_health.pack(side=tk.LEFT)
        
        self.badge_canvas = tk.Canvas(
            row_gw, 
            width=12, 
            height=12, 
            bg=self.theme["background"], 
            highlightthickness=0
        )
        self.badge_canvas.pack(side=tk.LEFT, padx=(8, 4))
        self.status_circle = self.badge_canvas.create_oval(
            1, 1, 11, 11, 
            fill=self.theme["error"], 
            width=0
        )
        
        self.status_text_lbl = tk.Label(
            row_gw, 
            text="Offline", 
            font=("Segoe UI", 9), 
            bg=self.theme["background"], 
            fg=self.theme["text_muted"]
        )
        self.status_text_lbl.pack(side=tk.LEFT)
        
        # 2. AI Mode
        row_ai = tk.Frame(status_card, bg=self.theme["background"])
        row_ai.pack(fill=tk.X, padx=12, pady=6)
        
        self.ai_mode_lbl = tk.Label(
            row_ai, 
            text="AI Mode: offline", 
            font=("Segoe UI", 9), 
            bg=self.theme["background"], 
            fg=self.theme["text_muted"]
        )
        self.ai_mode_lbl.pack(side=tk.LEFT)
        
        # 3. Core Version
        row_ver = tk.Frame(status_card, bg=self.theme["background"])
        row_ver.pack(fill=tk.X, padx=12, pady=6)
        
        self.version_lbl = tk.Label(
            row_ver, 
            text="Core V: 1.0", 
            font=("Segoe UI", 9), 
            bg=self.theme["background"], 
            fg=self.theme["text_muted"]
        )
        self.version_lbl.pack(side=tk.LEFT)
        
        # 4. Memory Footprint
        row_mem = tk.Frame(status_card, bg=self.theme["background"])
        row_mem.pack(fill=tk.X, padx=12, pady=6)
        
        self.memory_lbl = tk.Label(
            row_mem, 
            text="Memory: 142.0 MB / 512 MB", 
            font=("Segoe UI", 9), 
            bg=self.theme["background"], 
            fg=self.theme["text_muted"]
        )
        self.memory_lbl.pack(side=tk.LEFT)
        
        # Animated progress indicator (glowing bar)
        self.progress_canvas = tk.Canvas(
            left_frame, 
            height=3, 
            bg=self.theme["surface"], 
            highlightthickness=0
        )
        self.progress_canvas.pack(fill=tk.X, pady=(10, 10), padx=15)
        
        self.progress_track = self.progress_canvas.create_rectangle(
            0, 0, 1000, 3, 
            fill=self.theme["border"], 
            width=0
        )
        self.progress_bar = self.progress_canvas.create_rectangle(
            0, 0, 60, 3, 
            fill=self.theme["primary"], 
            width=0
        )
        self.progress_x = 0
        self.progress_dir = 1
        
        divider = tk.Frame(left_frame, height=1, bg=self.theme["border"])
        divider.pack(fill=tk.X, pady=10, padx=15)
        
        btn_container = tk.Frame(left_frame, bg=self.theme["surface"])
        btn_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Start/Stop buttons
        control_row = tk.Frame(btn_container, bg=self.theme["surface"])
        control_row.pack(fill=tk.X, pady=4)
        
        self.start_btn = self.create_flat_button(
            control_row, 
            text="Start Backend", 
            command=self.start_backend, 
            bg=self.theme["surface"], 
            fg=self.theme["success"],
            hover_bg=self.theme["border"]
        )
        self.start_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        
        self.stop_btn = self.create_flat_button(
            control_row, 
            text="Stop Backend", 
            command=self.stop_backend, 
            bg=self.theme["surface"], 
            fg=self.theme["error"],
            hover_bg=self.theme["border"]
        )
        self.stop_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))
        
        # Links
        self.docs_btn = self.create_flat_button(
            btn_container, 
            text="Open API Docs", 
            command=self.open_docs,
            bg=self.theme["border"],
            fg=self.theme["text"]
        )
        self.docs_btn.pack(fill=tk.X, pady=4)
        
        self.matrix_btn = self.create_flat_button(
            btn_container, 
            text="Open Live Matrix Dashboard", 
            command=self.open_matrix,
            bg=self.theme["border"],
            fg=self.theme["text"]
        )
        self.matrix_btn.pack(fill=tk.X, pady=4)
        
        # Task Console Padded Frame
        console_lbl = tk.Label(
            btn_container, 
            text="EXECUTE TASK CONSOLE", 
            font=("Segoe UI", 10, "bold"), 
            bg=self.theme["surface"], 
            fg=self.theme["primary"]
        )
        console_lbl.pack(anchor="w", pady=(15, 5))
        
        input_container = tk.Frame(
            btn_container, 
            bg=self.theme["background"], 
            highlightthickness=1, 
            highlightbackground=self.theme["border"]
        )
        input_container.pack(fill=tk.X, pady=(0, 6))
        
        self.input_entry = tk.Entry(
            input_container, 
            font=("Segoe UI", 11), 
            bg=self.theme["background"], 
            fg=self.theme["text"],
            bd=0,
            insertbackground=self.theme["text"],
            highlightthickness=0
        )
        self.input_entry.pack(fill=tk.X, padx=10, pady=10)
        self.input_entry.insert(0, "Jarvis'e görev ver")
        self.input_entry.bind("<FocusIn>", self.on_entry_focus_in)
        self.input_entry.bind("<FocusOut>", self.on_entry_focus_out)
        
        self.task_btn = self.create_flat_button(
            btn_container, 
            text="Gönder (Dry Run)", 
            command=self.send_task,
            bg=self.theme["primary"],
            fg=self.theme["background"],
            hover_bg=self.theme["accent"]
        )
        self.task_btn.pack(fill=tk.X, pady=4)
        
        # --- RIGHT COLUMN ---
        right_frame = tk.Frame(
            main_container, 
            bg=self.theme["background"], 
            bd=0
        )
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=0)
        
        # 1. Response Matrix Panel
        resp_lbl = tk.Label(
            right_frame, 
            text="TASK RESPONSE MATRIX", 
            font=("Segoe UI", 10, "bold"), 
            bg=self.theme["background"], 
            fg=self.theme["text_muted"]
        )
        resp_lbl.pack(anchor="w", pady=(0, 4))
        
        resp_container = tk.Frame(
            right_frame, 
            bg=self.theme["surface"],
            highlightthickness=1, 
            highlightbackground=self.theme["border"]
        )
        resp_container.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.response_viewer = ScrolledText(
            resp_container, 
            font=("Consolas", 10), 
            bg=self.theme["surface"], 
            fg=self.theme["primary"], 
            bd=0, 
            highlightthickness=0,
            relief="flat",
            wrap=tk.WORD,
            height=6
        )
        self.response_viewer.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.response_viewer.insert(tk.END, "{\n  \"status\": \"idle\",\n  \"waiting_for_task\": true\n}")
        self.response_viewer.config(state=tk.DISABLED)
        
        # 2. Real-time Log Stream
        log_lbl = tk.Label(
            right_frame, 
            text="RUNTIME LOG STREAM", 
            font=("Segoe UI", 10, "bold"), 
            bg=self.theme["background"], 
            fg=self.theme["text_muted"]
        )
        log_lbl.pack(anchor="w", pady=(0, 4))
        
        log_container = tk.Frame(
            right_frame, 
            bg=self.theme["surface"],
            highlightthickness=1, 
            highlightbackground=self.theme["border"]
        )
        log_container.pack(fill=tk.BOTH, expand=True)
        
        self.log_viewer = ScrolledText(
            log_container, 
            font=("Consolas", 10), 
            bg=self.theme["background"], 
            fg=self.theme["text"], 
            bd=0, 
            highlightthickness=0,
            relief="flat",
            wrap=tk.WORD,
            height=12
        )
        self.log_viewer.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.log_viewer.insert(tk.END, ">>> Connecting to core log channel...\n")
        self.log_viewer.config(state=tk.DISABLED)
        
        # Color configuring syntax logging tags
        self.log_viewer.tag_configure("info", foreground=self.theme["primary"])
        self.log_viewer.tag_configure("success", foreground=self.theme["success"])
        self.log_viewer.tag_configure("warn", foreground=self.theme["warning"])
        self.log_viewer.tag_configure("error", foreground=self.theme["error"])

    def create_flat_button(self, parent, text, command, bg, fg, hover_bg=None):
        btn = tk.Button(
            parent, 
            text=text, 
            command=command, 
            bg=bg, 
            fg=fg, 
            font=("Segoe UI", 10, "bold"), 
            relief="flat", 
            bd=0,
            cursor="hand2",
            padx=10, 
            pady=8,
            activebackground=hover_bg or self.theme["border"],
            activeforeground=fg
        )
        
        h_bg = hover_bg or self.theme["primary"]
        h_fg = self.theme["background"] if h_bg == self.theme["primary"] or h_bg == self.theme["accent"] else fg
        
        def on_enter(e):
            btn.config(bg=h_bg, fg=h_fg)
        def on_leave(e):
            btn.config(bg=bg, fg=fg)
            
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def on_entry_focus_in(self, event):
        if self.input_entry.get() == "Jarvis'e görev ver":
            self.input_entry.delete(0, tk.END)

    def on_entry_focus_out(self, event):
        if not self.input_entry.get():
            self.input_entry.insert(0, "Jarvis'e görev ver")

    # Title bar drag operations
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
                try:
                    self.root.overrideredirect(True)
                except Exception:
                    pass
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
                width = 950
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

    def animate_progress(self):
        try:
            width = self.progress_canvas.winfo_width() or 300
            self.progress_x += self.progress_dir * 3
            if self.progress_x > width - 60:
                self.progress_dir = -1
            elif self.progress_x < 0:
                self.progress_dir = 1
            self.progress_canvas.coords(
                self.progress_bar, 
                self.progress_x, 0, 
                self.progress_x + 60, 3
            )
            self.root.after(30, self.animate_progress)
        except Exception:
            pass

    def update_memory_usage(self):
        try:
            base = 142.5
            offset = random.uniform(-1.5, 1.5)
            self.memory_lbl.config(text=f"Memory: {base + offset:.1f} MB / 512 MB")
        except Exception:
            pass
        self.root.after(3000, self.update_memory_usage)

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
            self.log_viewer.config(state=tk.NORMAL)
            
            start_pos = self.log_viewer.index(tk.END + "-1c")
            self.log_viewer.insert(tk.END, text_line + "\n")
            end_pos = self.log_viewer.index(tk.END + "-1c")
            
            text_upper = text_line.upper()
            if "[INFO]" in text_upper:
                self.log_viewer.tag_add("info", start_pos, end_pos)
            elif "[SUCCESS]" in text_upper:
                self.log_viewer.tag_add("success", start_pos, end_pos)
            elif "[WARN]" in text_upper or "[WARNING]" in text_upper:
                self.log_viewer.tag_add("warn", start_pos, end_pos)
            elif "[ERROR]" in text_upper:
                self.log_viewer.tag_add("error", start_pos, end_pos)
                
            content = self.log_viewer.get("1.0", tk.END)
            if len(content.splitlines()) > 500:
                self.log_viewer.delete("1.0", "50.0")
            self.log_viewer.see(tk.END)
            self.log_viewer.config(state=tk.DISABLED)
        except Exception:
            pass

    def check_status(self):
        try:
            status = self.launcher.health_check()
            if status["status"] == "online":
                data = status.get("data", {})
                self.badge_canvas.itemconfig(self.status_circle, fill=self.theme["success"])
                self.status_text_lbl.config(text="Online", fg=self.theme["success"])
                
                ai_mode = data.get("ai_mode", "hybrid_deepseek_hermes")
                version = data.get("version", "1.0")
                self.ai_mode_lbl.config(text=f"AI Mode: {ai_mode}", fg=self.theme["primary"])
                self.version_lbl.config(text=f"Core V: {version}", fg=self.theme["text_muted"])
            else:
                self.badge_canvas.itemconfig(self.status_circle, fill=self.theme["error"])
                self.status_text_lbl.config(text="Offline", fg=self.theme["text_muted"])
                self.ai_mode_lbl.config(text="AI Mode: offline", fg=self.theme["text_muted"])
        except Exception:
            pass
        self.root.after(5000, self.check_status)

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
        webbrowser.open("http://127.0.0.1:8502")

    def send_task(self):
        task = self.input_entry.get()
        if not task or task == "Jarvis'e görev ver":
            messagebox.showwarning("Warning", "Lütfen geçerli bir görev girin.")
            return
            
        try:
            self.response_viewer.config(state=tk.NORMAL)
            self.response_viewer.delete("1.0", tk.END)
            self.response_viewer.insert(tk.END, "{\n  \"status\": \"processing\",\n  \"task\": \"" + task + "\"\n}")
            self.response_viewer.config(state=tk.DISABLED)
            
            resp = httpx.post(
                f"http://{self.launcher.host}:{self.launcher.port}/api/jarvis/task", 
                json={"task": task, "dry_run": True}, 
                timeout=10
            )
            
            resp_data = resp.json()
            formatted_json = json.dumps(resp_data, indent=2, ensure_ascii=False)
            
            self.response_viewer.config(state=tk.NORMAL)
            self.response_viewer.delete("1.0", tk.END)
            self.response_viewer.insert(tk.END, formatted_json)
            self.response_viewer.config(state=tk.DISABLED)
            
            messagebox.showinfo("Result", "Görev başarıyla gönderildi (Dry Run).")
        except Exception as e:
            self.response_viewer.config(state=tk.NORMAL)
            self.response_viewer.delete("1.0", tk.END)
            self.response_viewer.insert(tk.END, "{\n  \"error\": \"" + str(e).replace('"', '\\"') + "\"\n}")
            self.response_viewer.config(state=tk.DISABLED)
            messagebox.showerror("Error", str(e))

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
