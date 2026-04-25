#!/bin/bash
# ─────────────────────────────────────────────────────────
# DistriStore — Setup Script (Linux/macOS)
# Creates Python venv, installs backend deps, and npm deps
# ─────────────────────────────────────────────────────────
set -e

echo "=============================================="
echo "  DistriStore — Environment Setup"
echo "=============================================="

# 1. Python Virtual Environment
echo ""
echo "[1/3] Creating Python virtual environment..."
python3 -m venv .venv
echo "  ✅ .venv created"

# 2. Install Python dependencies
echo ""
echo "[2/3] Installing Python dependencies..."
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "  ✅ Python dependencies installed"

# 3. Install Frontend dependencies
echo ""
echo "[3/3] Installing Frontend dependencies..."
cd frontend
npm install --silent
cd ..
echo "  ✅ Frontend dependencies installed"

echo ""
echo "=============================================="
echo "  ✅ Setup complete!"
echo ""
echo "  To start DistriStore, run:"
echo "    ./start.sh"
echo "=============================================="
