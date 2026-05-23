@echo off
TITLE ZEZELABS JARVIS v4.0 — SİBER KARARGAH
color 0B
cd /d "C:\Users\Zezelabs2\.gemini\antigravity\scratch\zezelabs-brain"

echo.
echo  ██████  ███████ ███████ ███████
echo     ███  ██      ██         ███
echo    ███   █████   ███████   ███
echo   ███    ██           ██  ███
echo  ███████ ███████ ███████ ███████
echo.
echo  ZEZELABS SİBER KARARGAH — JARVIS v4.0
echo  ======================================
echo.

:: 1. Backend başlat (arka planda)
echo [1/3] Backend başlatılıyor...
start "JARVIS-BACKEND" /min cmd /c "python -m uvicorn backend.jarvis:app --port 8000 --log-level warning"

:: 2. 2 saniye bekle
timeout /t 2 /nobreak >nul

:: 3. PySide6 Desktop UI başlat
echo [2/3] PySide6 Siber Karargah başlatılıyor...
start "JARVIS-DESKTOP" /min cmd /c "python desktop\jarvis_desktop.py"

echo [3/3] Sistem hazır!
echo.
echo Masaüstünde ZEZELABS JARVIS penceresi açılıyor...
timeout /t 3 /nobreak >nul
