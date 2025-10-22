@echo off
REM Production startup script for Label Print Server
REM This script starts the production WSGI server

echo ====================================
echo Label Print Server - Production Mode
echo ====================================

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please create virtual environment first:
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

REM Check if required files exist
if not exist "wsgi.py" (
    echo ERROR: wsgi.py not found!
    pause
    exit /b 1
)

if not exist "app.py" (
    echo ERROR: app.py not found!
    pause
    exit /b 1
)

REM Set production environment
set FLASK_ENV=production
set LOG_LEVEL=INFO

echo Starting Label Print Server...
echo Environment: %FLASK_ENV%
echo Log Level: %LOG_LEVEL%
echo.

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Start the production server
".venv\Scripts\python.exe" wsgi.py

echo.
echo Label Print Server stopped.
pause