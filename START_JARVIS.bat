@echo off
TITLE ZEZELABS JARVIS v4.2 PRO
SETLOCAL

:: --- CONFIG ---
SET BACKEND_DIR=standalone_jarvis\backend
SET FRONTEND_DIR=standalone_jarvis\frontend

echo ======================================================
echo   ZEZELABS JARVIS v5.0 | STARTING SYSTEMS...
echo   TIP: Use 'python GHOST_LAUNCHER.py' for Ghost Mode!
echo ======================================================

:: 1. Start Backend in a new window
echo [SYSTEM] Starting Jarvis Brain (Python)...
start "Jarvis Backend" cmd /k "cd %BACKEND_DIR% && python jarvis.py"

:: 2. Wait a few seconds for backend
timeout /t 3 /nobreak > nul

:: 3. Start Frontend in a new window
echo [SYSTEM] Starting Jarvis Interface (Vite)...
start "Jarvis UI" cmd /k "cd %FRONTEND_DIR% && npm run dev"

echo.
echo ======================================================
echo   SYSTEMS ACTIVE. 
echo   Interface: http://localhost:5173
echo   Backend:   http://localhost:5000 (WS)
echo ======================================================
echo.
pause
