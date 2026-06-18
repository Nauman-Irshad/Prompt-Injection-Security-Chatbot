@echo off
title Prompt Injection Project - Install and Run
echo ============================================================
echo   PROMPT INJECTION PROJECT - INSTALL AND RUN
echo   Team: L1F22BSCS0122, 0929, 0939, 0909
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/5] Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 goto error

echo.
echo [2/5] Installing dependencies (may take a few minutes)...
pip install -r requirements.txt
if errorlevel 1 goto error

echo.
echo [3/5] Generating Word manual (PROJECT_MANUAL.docx)...
python scripts/generate_manual_docx.py
if errorlevel 1 echo Warning: Word manual generation skipped

echo.
echo [4/5] Verifying project...
python verify_project.py
if errorlevel 1 goto error

echo.
echo [5/5] Starting Security Chatbot...
echo.
echo   Open browser: http://localhost:5000
echo   Press Ctrl+C to stop the server
echo.
python run_chatbot.py
goto end

:error
echo.
echo ERROR: Setup failed. Make sure Python 3.10+ and Java are installed.
echo Install Java from: https://adoptium.net/
pause
exit /b 1

:end
