import os
import shutil
import sys

def main():
    base = os.getcwd()
    print(f"🚀 Physical Migration & Core Expansion starting in: {base}")
    
    # 1. Directory Structure Creation
    dirs = [
        "core/orchestrator",
        "core/config",
        "core/memory",
        "backend",
        "frontend",
        "logs"
    ]
    for d in dirs:
        path = os.path.join(base, d)
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"✅ Created directory: {d}")

    # 2. Move Files from standalone_jarvis
    mappings = {
        "standalone_jarvis/backend": "backend",
        "standalone_jarvis/frontend": "frontend"
    }
    
    for src, dst in mappings.items():
        s_path = os.path.join(base, src)
        d_path = os.path.join(base, dst)
        if os.path.exists(s_path):
            print(f"📦 Moving {src} contents to {dst}...")
            for item in os.listdir(s_path):
                s_item = os.path.join(s_path, item)
                d_item = os.path.join(d_path, item)
                try:
                    if os.path.exists(d_item):
                        if os.path.isdir(d_item): shutil.rmtree(d_item)
                        else: os.remove(d_item)
                    shutil.move(s_item, d_item)
                except Exception as e:
                    print(f"⚠️ Error moving {item}: {e}")
            print(f"✅ {dst} populated.")

    print("\n[SUCCESS] Physical migration complete. Ready for Core Logic injection.")

if __name__ == "__main__":
    main()
