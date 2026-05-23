Set WshShell = CreateObject("WScript.Shell")

' 1. Start FastAPI backend silently (0 = hide window, false = don't wait for exit)
WshShell.Run "cmd /c cd /d C:\Users\Zezelabs2\.gemini\antigravity\scratch\zezelabs-brain && C:\Python314\python.exe -m uvicorn backend.jarvis:app --port 8000", 0, false

' 2. Sleep for 2 seconds for backend port binding
WScript.Sleep 2000

' 3. Launch PySide6 Jarvis Desktop
WshShell.Run "cmd /c cd /d C:\Users\Zezelabs2\.gemini\antigravity\scratch\zezelabs-brain && C:\Python314\python.exe desktop\jarvis_desktop.py", 0, false
