@echo off
echo ============================================================
echo   PROMPT INJECTION PROJECT - FULL DEMO
echo   Team: L1F22BSCS0122, 0929, 0939, 0909
echo ============================================================
echo.
cd /d "%~dp0"
echo [1/3] Verifying project...
python verify_project.py
echo.
echo [2/3] Running all attack and defense demos...
python run_all.py
echo.
echo [3/3] Starting chatbot server...
echo Open http://localhost:5000 in your browser
python run_chatbot.py
