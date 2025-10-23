@echo off
REM Remove Label Print Server from Windows Startup
REM This script removes auto-startup configuration

echo ========================================
echo   Remove Label Print Server Auto-Startup
echo ========================================
echo.

REM Change to script directory
cd /d "%~dp0"

echo Are you sure you want to remove Label Print Server from auto-startup?
echo This will prevent the tray icon from starting automatically with Windows.
echo.
set /p confirm="Type 'yes' to confirm removal: "

if /i not "%confirm%"=="yes" (
    echo.
    echo ❌ Operation cancelled.
    echo The auto-startup configuration remains unchanged.
    pause
    exit /b 0
)

echo.
echo Removing auto-startup configuration...

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo ❌ Virtual environment not found!
    echo Please run this from the Label Print Server directory.
    pause
    exit /b 1
)

REM Remove auto-startup
.venv\Scripts\python.exe auto_startup.py uninstall
if errorlevel 1 (
    echo ❌ Failed to remove auto-startup configuration
    pause
    exit /b 1
)

echo.
echo ========================================
echo    ✅ Auto-Startup Removed Successfully
echo ========================================
echo.
echo 📋 What was changed:
echo   • Removed registry entry for automatic startup
echo   • Tray icon will no longer start with Windows
echo   • Application files remain unchanged
echo.
echo 🚀 To start manually:
echo   • Double-click: start_tray_silent.vbs
echo   • Use desktop shortcut: "Label Print Server"
echo   • Command line: python tray_app.py
echo.
echo 💡 To re-enable auto-startup later:
echo   • Run: setup.bat (complete setup)
echo   • Or: python auto_startup.py install
echo.
pause