import shutil
import os

src = r"C:\Users\Zezelabs2\.gemini\antigravity\brain\d31b83f3-49db-4023-8dcf-b4c3bc6b8268\scifi_office_cutaway_1778628438645.png"
dst_dir = r"c:\Users\Zezelabs2\.gemini\antigravity\scratch\zezelabs-brain\live_matrix\frontend\public"

os.makedirs(dst_dir, exist_ok=True)
shutil.copy2(src, os.path.join(dst_dir, "bg.png"))
print("New CUTAWAY background image copied successfully to public/bg.png!")
