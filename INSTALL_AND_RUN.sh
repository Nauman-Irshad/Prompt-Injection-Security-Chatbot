#!/bin/bash
set -e
echo "============================================================"
echo "  PROMPT INJECTION PROJECT - INSTALL AND RUN"
echo "  Team: L1F22BSCS0122, 0929, 0939, 0909"
echo "============================================================"

cd "$(dirname "$0")"

echo "[1/5] Upgrading pip..."
python3 -m pip install --upgrade pip

echo "[2/5] Installing dependencies..."
pip3 install -r requirements.txt

echo "[3/5] Generating Word manual..."
python3 scripts/generate_manual_docx.py || true

echo "[4/5] Verifying project..."
python3 verify_project.py

echo "[5/5] Starting Security Chatbot..."
echo "  Open browser: http://localhost:5000"
python3 run_chatbot.py
