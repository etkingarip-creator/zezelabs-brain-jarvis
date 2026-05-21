import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
import httpx
import webbrowser
from queue import Queue, Empty

from desktop.backend_launcher import BackendLauncher
from desktop.theme.colors import get_theme
from desktop.sse_client import SSELogClient

class JarvisDesktopApp:
    def __init__(self, root):
        self.root = root
        self.theme = get_theme()
        
        # Window configuration
        self.root.title("Jarvis Desktop OS")
        self.root.geometry("850x580")
        self.root.configure(bg=self.theme["background"])
        
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
        
        # Clean shutdown handling
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        # Configure grid weight for responsiveness
        self.root.columnconfigure(0, weight=4) # Left pane
        self.root.columnconfigure(1, weight=6) # Right pane
        self.root.rowconfigure(0, weight=1)
        
        # --- LEFT PANE (Controls) ---
        left_frame = tk.Frame(
            self.root, 
            bg=self.theme["surface"], 
            bd=0, 
            highlightthickness=1, 
            highlightbackground=self.theme["border"]
        )
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        
        # Title Header
        title_label = tk.Label(
            left_frame, 
            text="JARVIS OS", 
            font=("Segoe UI", 22, "bold"), 
            bg=self.theme["surface"], 
            fg=self.theme["primary"]
        )
        title_label.pack(pady=(20, 2))
        
        subtitle_label = tk.Label(
            left_frame, 
            text="Zezelabs Operating System Core", 
            font=("Segoe UI", 9), 
            bg=self.theme["surface"], 
            fg=self.theme["text_muted"]
        )
        subtitle_label.pack(pady=(0, 15))
        
        # System Health Status Widget
        status_container = tk.Frame(left_frame, bg=self.theme["surface"])
        status_container.pack(pady=10, fill=tk.X, padx=10)
        
        status_lbl_title = tk.Label(
            status_container, 
            text="System Core Status:", 
            font=("Segoe UI", 11, "bold"), 
            bg=self.theme["surface"], 
            fg=self.theme["text"]
        )
        status_lbl_title.pack(side=tk.LEFT, padx=(15, 5))
        
        # Dynamic Badge (Canvas circle indicator)
        self.badge_canvas = tk.Canvas(
            status_container, 
            width=16, 
            height=16, 
            bg=self.theme["surface"], 
            highlightthickness=0
        )
        self.badge_canvas.pack(side=tk.LEFT, padx=(5, 5))
        self.status_circle = self.badge_canvas.create_oval(
            2, 2, 14, 14, 
            fill=self.theme["error"], 
            width=0
        )
        
        self.status_text_lbl = tk.Label(
            status_container, 
            text="Offline", 
            font=("Segoe UI", 11), 
            bg=self.theme["surface"], 
            fg=self.theme["text_muted"]
        )
        self.status_text_lbl.pack(side=tk.LEFT, padx=(5, 5))
        
        # Animated progress indicator (glowing bar)
        self.progress_canvas = tk.Canvas(
            left_frame, 
            height=4, 
            bg=self.theme["surface"], 
            highlightthickness=0
        )
        self.progress_canvas.pack(fill=tk.X, pady=(15, 15), padx=25)
        
        self.progress_track = self.progress_canvas.create_rectangle(
            0, 0, 1000, 4, 
            fill=self.theme["border"], 
            width=0
        )
        self.progress_bar = self.progress_canvas.create_rectangle(
            0, 0, 50, 4, 
            fill=self.theme["primary"], 
            width=0
        )
        self.progress_x = 0
        self.progress_dir = 1
        
        # Divider Line
        divider = tk.Frame(left_frame, height=1, bg=self.theme["border"])
        divider.pack(fill=tk.X, pady=10, padx=20)
        
        # Control Buttons Container
        btn_container = tk.Frame(left_frame, bg=self.theme["surface"])
        btn_container.pack(fill=tk.BOTH, expand=True, padx=20)
        
        # Start/Stop buttons in same row
        control_row = tk.Frame(btn_container, bg=self.theme["surface"])
        control_row.pack(fill=tk.X, pady=5)
        
        self.start_btn = self.create_flat_button(
            control_row, 
            text="Start Backend", 
            command=self.start_backend, 
            bg=self.theme["surface"], 
            fg=self.theme["success"],
            hover_bg=self.theme["border"]
        )
        self.start_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.stop_btn = self.create_flat_button(
            control_row, 
            text="Stop Backend", 
            command=self.stop_backend, 
            bg=self.theme["surface"], 
            fg=self.theme["error"],
            hover_bg=self.theme["border"]
        )
        self.stop_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Helper links
        self.docs_btn = self.create_flat_button(
            btn_container, 
            text="Open API Docs", 
            command=self.open_docs,
            bg=self.theme["border"],
            fg=self.theme["text"]
        )
        self.docs_btn.pack(fill=tk.X, pady=5)
        
        self.matrix_btn = self.create_flat_button(
            btn_container, 
            text="Open Live Matrix Dashboard", 
            command=self.open_matrix,
            bg=self.theme["border"],
            fg=self.theme["text"]
        )
        self.matrix_btn.pack(fill=tk.X, pady=5)
        
        # Rounded flat-look Entry input box
        input_container = tk.Frame(
            btn_container, 
            bg=self.theme["background"], 
            highlightthickness=1, 
            highlightbackground=self.theme["border"]
        )
        input_container.pack(fill=tk.X, pady=(20, 10))
        
        self.input_entry = tk.Entry(
            input_container, 
            font=("Segoe UI", 11), 
            bg=self.theme["background"], 
            fg=self.theme["text"],
            bd=0,
            insertbackground=self.theme["text"],
            highlightthickness=0
        )
        self.input_entry.pack(fill=tk.X, padx=10, pady=8)
        self.input_entry.insert(0, "Jarvis'e görev ver")
        
        # Placeholder text helper
        self.input_entry.bind("<FocusIn>", self.on_entry_focus_in)
        self.input_entry.bind("<FocusOut>", self.on_entry_focus_out)
        
        self.task_btn = self.create_flat_button(
            btn_container, 
            text="Gönder (Dry Run)", 
            command=self.send_task,
            bg=self.theme["primary"],
            fg=self.theme["background"],
            hover_bg=self.theme["secondary"]
        )
        self.task_btn.pack(fill=tk.X, pady=5)
        
        # --- RIGHT PANE (Real-time Log Viewer) ---
        right_frame = tk.Frame(
            self.root, 
            bg=self.theme["background"], 
            bd=0
        )
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        
        log_title = tk.Label(
            right_frame, 
            text="RUNTIME LOG STREAM", 
            font=("Segoe UI", 10, "bold"), 
            bg=self.theme["background"], 
            fg=self.theme["text_muted"]
        )
        log_title.pack(anchor="w", pady=(10, 5), padx=5)
        
        # Log viewer container frame
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
            wrap=tk.WORD
        )
        self.log_viewer.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_viewer.insert(tk.END, ">>> Connecting to core log channel...\n")
        self.log_viewer.config(state=tk.DISABLED)

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
        h_fg = self.theme["background"] if h_bg == self.theme["primary"] else fg
        
        # Micro-animations on hover (bind <Enter> and <Leave>)
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

    def animate_progress(self):
        try:
            width = self.progress_canvas.winfo_width() or 300
            self.progress_x += self.progress_dir * 3
            if self.progress_x > width - 50:
                self.progress_dir = -1
            elif self.progress_x < 0:
                self.progress_dir = 1
            self.progress_canvas.coords(
                self.progress_bar, 
                self.progress_x, 0, 
                self.progress_x + 50, 4
            )
            self.root.after(30, self.animate_progress)
        except Exception:
            pass

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
            self.log_viewer.insert(tk.END, text_line + "\n")
            # Limit the content size to prevent high memory usage
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
                self.badge_canvas.itemconfig(self.status_circle, fill=self.theme["success"])
                self.status_text_lbl.config(text="Online", fg=self.theme["success"])
            else:
                self.badge_canvas.itemconfig(self.status_circle, fill=self.theme["error"])
                self.status_text_lbl.config(text="Offline", fg=self.theme["text_muted"])
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
            resp = httpx.post(
                f"http://{self.launcher.host}:{self.launcher.port}/api/jarvis/task", 
                json={"task": task, "dry_run": True}, 
                timeout=10
            )
            messagebox.showinfo("Result", str(resp.json()))
        except Exception as e:
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
