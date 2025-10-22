@echo off
REM Run the Label Print Server as a tray application with virtual environment
REM This file is designed to start the tray app on Windows startup

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo Error: Virtual environment not found. Please run setup first.
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate
    pip install -r requirements.txt
)

REM Start the tray application with virtual environment
echo Starting Label Print Server Tray Application...
".venv\Scripts\python.exe" tray_app.py

REM If we get here, the app has closed
echo Label Print Server has stopped.