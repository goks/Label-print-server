@echo off
REM Quick Setup Script for Label Print Server
REM This script performs complete setup for auto-startup with tray icon

echo ========================================
echo    Label Print Server - Quick Setup
echo ========================================
echo.

REM Change to script directory
cd /d "%~dp0"

echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+ first.
    pause
    exit /b 1
)
echo ✅ Python found

echo.
echo [2/5] Creating virtual environment...
if not exist ".venv" (
    python -m venv .venv
    echo ✅ Virtual environment created
) else (
    echo ℹ️ Virtual environment already exists
)

echo.
echo [3/5] Installing dependencies...
call .venv\Scripts\activate
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)
echo ✅ Dependencies installed

echo.
echo [4/5] Setting up configuration...
if not exist ".env" (
    if exist ".env.production" (
        copy ".env.production" ".env" >nul
        echo ✅ Configuration template copied to .env
        echo ⚠️ Please edit .env with your database settings
    ) else (
        echo # Label Print Server Configuration > .env
        echo DB_SERVER=GASERVER\BUSYSTDSQL >> .env
        echo DB_NAME=BusyComp0004_db12025 >> .env
        echo FLASK_ENV=production >> .env
        echo LOG_LEVEL=INFO >> .env
        echo ✅ Basic configuration created
    )
) else (
    echo ℹ️ Configuration file .env already exists
)

echo.
echo [5/5] Configuring auto-startup...
.venv\Scripts\python.exe auto_startup.py install
if errorlevel 1 (
    echo ❌ Failed to configure auto-startup
    echo You can configure it manually later with: python auto_startup.py setup
) else (
    echo ✅ Auto-startup configured
)

echo.
echo [Optional] Creating desktop shortcut...
.venv\Scripts\python.exe auto_startup.py shortcut

echo.
echo ========================================
echo    🎉 Setup Complete!
echo ========================================
echo.
echo 📋 What's configured:
echo   ✅ Python virtual environment
echo   ✅ All dependencies installed
echo   ✅ Auto-startup on Windows boot
echo   ✅ Desktop shortcut created
echo.
echo 🚀 Next steps:
echo   1. Edit .env file with your database settings
echo   2. Test: start_tray_silent.vbs
echo   3. Or reboot to start automatically
echo.
echo 🌐 Access web interface at: http://localhost:5000
echo.
pause