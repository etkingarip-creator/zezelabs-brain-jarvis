import os
import subprocess
import sys
import time
import signal
import logging

# PROKOTOL: ZOM FINAL BOOT
PID_FILE = "jarvis.pid"
LOG_FILE = "logs/boot.log"

os.makedirs("logs", exist_ok=True)
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')

def kill_previous_instance():
    """Kanıt: Sadece PID dosyasındaki process'i öldürür."""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                old_pid = int(f.read().strip())
            
            print(f"🔍 Eski PID bulundu: {old_pid}. Sonlandırılıyor...")
            if sys.platform == "win32":
                # Windows safe kill
                subprocess.run(["taskkill", "/F", "/PID", str(old_pid)], capture_output=True, stderr=subprocess.DEVNULL)
            else:
                os.kill(old_pid, signal.SIGTERM)
            
            print(f"✅ Eski instance (PID {old_pid}) sonlandırıldı.")
        except Exception as e:
            print(f"⚠️ Eski process bulunamadı veya zaten kapalı.")
        finally:
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)

def start():
    kill_previous_instance()
    
    # Mevcut PID'i kaydet
    current_pid = os.getpid()
    with open(PID_FILE, "w") as f:
        f.write(str(current_pid))
    
    print(f"🚀 Zezelabs Jarvis Başlatıldı (PID: {current_pid})")
    print(f"📂 Çalışma Dizini: {os.getcwd()}")
    
    # Backend'i başlat
    backend_script = os.path.join("backend", "jarvis.py")
    if os.path.exists(backend_script):
        print("⚙️ Backend ateşleniyor...")
        subprocess.Popen([sys.executable, backend_script], creationflags=0x08000000 if sys.platform == "win32" else 0)
    else:
        print("❌ HATA: backend/jarvis.py bulunamadı!")

if __name__ == "__main__":
    start()
