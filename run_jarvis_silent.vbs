Set WshShell = CreateObject("WScript.Shell")

' 1. Start FastAPI backend silently (0 = hide window, false = don't wait for exit)
WshShell.Run "cmd /c python -m uvicorn backend.jarvis:app --port 8000", 0, false

' 2. Sleep for 3 seconds for backend port binding
WScript.Sleep 3000

' 3. Launch Tauri application dev server silently (Vite + WebGL)
WshShell.Run "cmd /c cd jarvis-client && npm run tauri dev", 0, false
