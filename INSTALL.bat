@echo off
REM Label Print Server - Production Installer
title Label Print Server - Installation Wizard
setlocal enabledelayedexpansion

REM Change to script directory
cd /d "%~dp0"

REM Colors (for Windows 10+)
color 0A

echo.
echo ================================================================
echo            Label Print Server - Installation Wizard
echo ================================================================
echo.

REM Check for administrative privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running with administrative privileges
) else (
    echo [WARNING] Not running as administrator
    echo           Some features may require admin rights
)
echo.

REM Check Python installation
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8 or higher:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
python --version
echo.

REM Check/Create virtual environment
echo [2/5] Setting up virtual environment...
if exist ".venv\Scripts\python.exe" (
    echo [OK] Virtual environment already exists
) else (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)
echo.

REM Install/Update dependencies
echo [3/5] Installing dependencies...
echo This may take a few minutes...

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found in current directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
".venv\Scripts\pip.exe" install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    echo.
    echo Trying verbose installation to show errors...
    ".venv\Scripts\pip.exe" install -r requirements.txt
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

REM Initialize database
echo [4/5] Initializing database...
".venv\Scripts\python.exe" -c "from printed_db import init_db; init_db(); print('[OK] Database initialized')"
echo.

REM Run GUI installer
echo [5/5] Starting graphical installer...
echo.
".venv\Scripts\pythonw.exe" setup_installer.py

if errorlevel 1 (
    echo.
    echo [WARNING] Installation wizard closed
    echo.
    echo You can run the application manually with:
    echo    .venv\Scripts\python.exe tray_app_v2.py
    echo.
) else (
    echo.
    echo ================================================================
    echo            Installation completed successfully!
    echo ================================================================
    echo.
    echo The Label Print Server has been installed.
    echo Check your system tray for the application icon.
    echo.
)

pause
exit /b 0
