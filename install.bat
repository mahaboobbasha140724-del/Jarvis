@echo off
title J.A.R.V.I.S Installation Setup
echo ============================================================
echo  J.A.R.V.I.S: Arc Reactor Edition - Installation Setup
echo ============================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your system PATH!
    echo Please install Python 3.10 or higher from python.org and check
    echo the box "Add Python to PATH" during installation.
    echo.
    goto end
)

:: Check if venv directory exists, if not create it
if not exist "venv" (
    echo [INFO] Creating Python virtual environment (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment!
        goto end
    )
    echo [SUCCESS] Virtual environment created.
)

:: Activate virtual environment and install requirements
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

echo [INFO] Installing required libraries from requirements.txt...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install python dependencies!
    goto end
)

echo [INFO] Installing Playwright browsers...
python -m playwright install
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Playwright browsers!
    goto end
)

echo.
echo ============================================================
echo  Setup Complete! JARVIS is ready to use!
echo ============================================================
echo.
echo To start the web dashboard, run:
echo    python web_main.py
echo.
echo To build the standalone desktop app (.exe), run:
echo    python build_desktop.py
echo ============================================================
echo.

:end
echo Press any key to exit...
pause >nul
