@echo off
REM Safe startup script for Label Print Server tray app
REM Ensures clean startup by checking for existing processes

cd /d "%~dp0"

echo ========================================
echo   Label Print Server - Safe Startup
echo ========================================
echo.

REM Step 1: Check for and kill existing Python processes
echo [1/4] Checking for existing processes...
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *tray_app*" /NH 2^>nul') do (
    echo   Found existing process (PID: %%i), stopping...
    taskkill /PID %%i /F >nul 2>&1
)

REM Step 2: Clean up tray control files
echo [2/4] Cleaning up control files...
if exist ".tray_running" del /f /q ".tray_running" >nul 2>&1
if exist ".tray_control_token" del /f /q ".tray_control_token" >nul 2>&1
if exist ".tray_stop_signal" del /f /q ".tray_stop_signal" >nul 2>&1
if exist ".tray_start_signal" del /f /q ".tray_start_signal" >nul 2>&1
if exist ".tray_quit_signal" del /f /q ".tray_quit_signal" >nul 2>&1
echo   Cleanup complete

REM Step 3: Wait for processes to fully terminate
echo [3/4] Waiting for cleanup...
timeout /t 2 /nobreak >nul

REM Step 4: Start the tray app
echo [4/4] Starting tray app...
echo.
start "" ".venv\Scripts\pythonw.exe" tray_app.py

REM Wait a moment to check if it started
timeout /t 3 /nobreak >nul

REM Verify it's running
tasklist /FI "IMAGENAME eq pythonw.exe" | find "pythonw.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ Tray app started successfully!
    echo   Check your system tray for the icon.
) else (
    echo ✗ Tray app may not have started. Check logs for errors.
)

echo.
echo ========================================
pause
