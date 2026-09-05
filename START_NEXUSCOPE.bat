@echo off
setlocal
title NEXUSCOPE - One Click Launcher
cd /d "%~dp0"

echo.
echo  ==========================================
echo       NEXUSCOPE - AI INCIDENT COPILOT
echo  ==========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python is not installed.
  echo Install Python from https://www.python.org/downloads/
  pause
  exit /b 1
)

where node >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js is not installed.
  echo Install Node.js from https://nodejs.org/
  pause
  exit /b 1
)

echo [1/4] Preparing Python environment...
cd backend
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
)
call .venv\Scripts\activate.bat
echo [2/4] Installing backend packages...
python -m pip install -r requirements.txt
start "NEXUSCOPE Backend" cmd /k "cd /d "%~dp0backend" && call .venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8000"

cd ..\frontend
echo [3/4] Installing frontend packages...
if not exist "node_modules" (
  call npm install
)
echo [4/4] Starting NEXUSCOPE...
start "NEXUSCOPE Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

timeout /t 5 /nobreak >nul
start "" "http://localhost:5173"

echo.
echo NEXUSCOPE is starting.
echo Browser: http://localhost:5173
echo.
echo Keep the two black terminal windows open while using the app.
pause
