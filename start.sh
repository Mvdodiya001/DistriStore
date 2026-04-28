#!/bin/bash
# ─────────────────────────────────────────────────────────
# DistriStore — Start Script (Linux/macOS)
# Starts backend (FastAPI) in background + frontend (Vite)
# ─────────────────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
source .venv/bin/activate

echo "=============================================="
echo "  DistriStore — Starting Services"
echo "=============================================="

# 1. Start Backend (background) — uses config.yaml port with fallback
echo ""
echo "[1/2] Starting backend (FastAPI)..."
python -m backend.main &
BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID"
sleep 2

# Verify backend started
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo "  ✅ Backend running (port from config.yaml)"
else
    echo "  ❌ Backend failed to start"
    exit 1
fi

# 2. Start Frontend (foreground)
echo ""
echo "[2/2] Starting frontend (Vite dev server)..."
echo "  Dashboard will be at http://localhost:5173"
echo ""
cd frontend
npm run dev -- --host

# Cleanup backend on exit
kill $BACKEND_PID 2>/dev/null
echo "DistriStore stopped."
