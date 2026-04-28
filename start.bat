@echo off
REM ─────────────────────────────────────────────────────────
REM DistriStore — Start Script (Windows)
REM Opens backend in a new window + frontend in current window
REM ─────────────────────────────────────────────────────────

echo ==============================================
echo   DistriStore — Starting Services
echo ==============================================

REM 1. Start Backend (new window)
echo.
echo [1/2] Starting backend (FastAPI) in new window...
start cmd /k "call .venv\Scripts\activate && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"
echo   Backend starting at http://localhost:8000

REM Wait for backend to initialize
timeout /t 3 /nobreak > nul

REM 2. Start Frontend (current window)
echo.
echo [2/2] Starting frontend (Vite dev server)...
echo   Dashboard will be at http://localhost:5173
echo.
cd frontend
call ..\\.venv\Scripts\activate
npm run dev -- --host
