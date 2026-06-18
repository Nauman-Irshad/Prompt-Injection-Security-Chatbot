@echo off
title Security Chatbot - Start Server
cd /d "%~dp0"
echo ============================================================
echo   PROMPT INJECTION SECURITY CHATBOT
echo   Open browser: http://localhost:5000
echo   Press Ctrl+C to stop
echo ============================================================
python run_chatbot.py
pause
