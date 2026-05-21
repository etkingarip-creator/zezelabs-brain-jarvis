import tkinter as tk
from tkinter import messagebox
from desktop.backend_launcher import BackendLauncher

class JarvisDesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Jarvis Desktop")
        self.root.geometry("400x350")
        self.launcher = BackendLauncher()
        
        self.status_lbl = tk.Label(root, text="Status: Checking...", font=("Arial", 12))
        self.status_lbl.pack(pady=10)
        
        self.start_btn = tk.Button(root, text="Start Backend", command=self.start_backend, width=20)
        self.start_btn.pack(pady=5)
        
        self.stop_btn = tk.Button(root, text="Stop Backend", command=self.stop_backend, width=20)
        self.stop_btn.pack(pady=5)
        
        self.docs_btn = tk.Button(root, text="Open API Docs", command=self.open_docs, width=20)
        self.docs_btn.pack(pady=5)
        
        self.matrix_btn = tk.Button(root, text="Open Live Matrix", command=self.open_matrix, width=20)
        self.matrix_btn.pack(pady=5)
        
        self.input_entry = tk.Entry(root, width=40)
        self.input_entry.pack(pady=10)
        self.input_entry.insert(0, "Jarvis'e görev ver")
        
        self.task_btn = tk.Button(root, text="Gönder (Dry Run)", command=self.send_task, width=20)
        self.task_btn.pack(pady=5)
        
        self.check_status()

    def check_status(self):
        status = self.launcher.health_check()
        if status["status"] == "online":
            self.status_lbl.config(text="Status: Online", fg="green")
        else:
            self.status_lbl.config(text="Status: Offline", fg="red")
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
        import webbrowser
        webbrowser.open("http://127.0.0.1:8502")

    def send_task(self):
        task = self.input_entry.get()
        import httpx
        try:
            resp = httpx.post(f"http://{self.launcher.host}:{self.launcher.port}/api/jarvis/task", json={"task": task, "dry_run": True}, timeout=10)
            messagebox.showinfo("Result", str(resp.json()))
        except Exception as e:
            messagebox.showerror("Error", str(e))

def main():
    try:
        root = tk.Tk()
        app = JarvisDesktopApp(root)
        root.mainloop()
    except Exception as e:
        print("Failed to start GUI:", e)

if __name__ == "__main__":
    main()
