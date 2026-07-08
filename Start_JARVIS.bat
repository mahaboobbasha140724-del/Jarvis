@echo off
title Starting J.A.R.V.I.S...
echo ============================================================
echo  Starting J.A.R.V.I.S: Arc Reactor Dashboard
echo ============================================================
echo.

:: Check if virtual environment exists
if not exist "venv" (
    echo [ERROR] Virtual environment 'venv' not found!
    echo Please run 'install.bat' first to install JARVIS.
    echo.
    pause
    exit /b
)

:: Activate venv
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

:: Open the browser dashboard automatically
echo [INFO] Opening dashboard in your default browser...
start "" "http://localhost:8000"

:: Start the python web server
echo [INFO] Launching JARVIS Engine...
echo.
python web_main.py

echo.
echo ============================================================
echo  JARVIS has shut down.
echo ============================================================
pause
