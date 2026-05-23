@echo off
TITLE ZEZELABS JARVIS BACKEND
python -m uvicorn backend.jarvis:app --port 8000
pause
