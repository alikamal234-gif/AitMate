@echo off
title AitMate Desktop AI Assistant
echo ==============================================================
echo    AitMate Desktop AI Assistant - Starting Background Services
echo ==============================================================
echo.

REM 1. Check if backend is running, if not start it in background
curl -s http://127.0.0.1:8000/api/v1/health >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [*] Starting FastAPI AI Agent backend on http://127.0.0.1:8000 ...
    start /B python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
) else (
    echo [v] Backend is already active on 127.0.0.1:8000.
)

REM 2. Check if Vite dev server is running, if not start it
curl -s http://localhost:5173/ >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [*] Starting Vite Frontend on http://localhost:5173 ...
    start /B npm run dev
) else (
    echo [v] Frontend is already active on http://localhost:5173.
)

REM 3. Launch Windows System Tray Companion in background (pythonw runs silently without a black console window)
echo [*] Launching Windows System Tray Companion...
start "" pythonw scripts/aitmate_tray.py

echo.
echo ==============================================================
echo [SUCCESS] AitMate is now active!
echo  - Look at the bottom-right of your Windows screen (System Tray near clock).
echo  - Press Alt + A from ANY program to summon your AI Assistant!
echo  - Or click the tray icon to open AitMate.
echo ==============================================================
timeout /t 4 >nul
