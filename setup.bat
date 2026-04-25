@echo off
REM ─────────────────────────────────────────────────────────
REM DistriStore — Setup Script (Windows)
REM Creates Python venv, installs backend deps, and npm deps
REM ─────────────────────────────────────────────────────────

echo ==============================================
echo   DistriStore — Environment Setup
echo ==============================================

REM 1. Python Virtual Environment
echo.
echo [1/3] Creating Python virtual environment...
python -m venv .venv
echo   Done.

REM 2. Install Python dependencies
echo.
echo [2/3] Installing Python dependencies...
call .venv\Scripts\activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo   Done.

REM 3. Install Frontend dependencies
echo.
echo [3/3] Installing Frontend dependencies...
cd frontend
npm install --silent
cd ..
echo   Done.

echo.
echo ==============================================
echo   Setup complete!
echo.
echo   To start DistriStore, run:
echo     start.bat
echo ==============================================
