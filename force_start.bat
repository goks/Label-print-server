@echo off
REM Force Start - Kills all processes and starts fresh

cd /d "%~dp0"

echo ========================================
echo   Force Start Label Print Server
echo ========================================
echo.

echo [1/3] Killing all Python processes from this app...
for /f "tokens=2" %%i in ('wmic process where "commandline like '%%Label-print-server%%' and name='python.exe'" get processid 2^>nul ^| findstr /r "[0-9]"') do (
    echo   Killing PID %%i
    taskkill /PID %%i /F >nul 2>&1
)
for /f "tokens=2" %%i in ('wmic process where "commandline like '%%Label-print-server%%' and name='pythonw.exe'" get processid 2^>nul ^| findstr /r "[0-9]"') do (
    echo   Killing PID %%i
    taskkill /PID %%i /F >nul 2>&1
)
echo   Done

echo.
echo [2/3] Cleaning up control files...
del /f /q .tray_* >nul 2>&1
del /f /q .gui_running >nul 2>&1
echo   Done

echo.
echo [3/3] Waiting for cleanup...
timeout /t 2 /nobreak >nul

echo.
echo Starting tray app...
start "" ".venv\Scripts\pythonw.exe" tray_app.py

timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo   Startup Complete!
echo   Check your system tray for the icon
echo ========================================
echo.
pause
