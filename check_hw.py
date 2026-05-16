import psutil
import platform
import os

def get_hw():
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"CPU: {platform.processor()}")
    print(f"Physical Cores: {psutil.cpu_count(logical=False)}")
    print(f"Total Cores: {psutil.cpu_count(logical=True)}")
    mem = psutil.virtual_memory()
    print(f"Total RAM: {round(mem.total / (1024**3), 2)} GB")
    print(f"Available RAM: {round(mem.available / (1024**3), 2)} GB")

if __name__ == "__main__":
    get_hw()
