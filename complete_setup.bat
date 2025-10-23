@echo off
REM Complete Setup Script for Label Print Server
REM This script handles installation, configuration, and startup setup

echo ========================================
echo  Label Print Server - Complete Setup
echo ========================================
echo.

cd /d "%~dp0"

REM Check if Python virtual environment exists
if not exist ".venv" (
    echo 🐍 Creating Python virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        echo Please ensure Python is installed and accessible
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

REM Activate virtual environment and install dependencies
echo 📦 Installing dependencies...
.\.venv\Scripts\pip.exe install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)
echo ✅ Dependencies installed

REM Create logs directory if it doesn't exist
if not exist "logs" (
    mkdir logs
    echo ✅ Created logs directory
)

REM Create initial configuration if it doesn't exist
if not exist "db_settings.json" (
    echo 📝 Creating default database configuration...
    echo {"server": "localhost", "database": "YourDatabase", "last_check": null} > db_settings.json
    echo ✅ Default configuration created
    echo ⚠️  Please update db_settings.json with your database details
)

REM Initialize update configuration
echo 🔄 Configuring update system...
.\.venv\Scripts\python.exe update_manager.py config
if errorlevel 1 (
    echo ❌ Failed to initialize update configuration
) else (
    echo ✅ Update system configured
)

REM Check for updates
echo 🔍 Checking for updates...
.\.venv\Scripts\python.exe update_manager.py check --force

REM Setup menu
:menu
echo.
echo ========================================
echo           Setup Options
echo ========================================
echo   1. Run Label Print Server (Web Mode)
echo   2. Run in System Tray Mode
echo   3. Enable Auto-Startup (recommended)
echo   4. Open Configuration GUI
echo   5. Test Database Connection
echo   6. Check System Status
echo   7. Exit Setup
echo.
set /p choice="Select option (1-7): "

if "%choice%"=="1" goto run_web
if "%choice%"=="2" goto run_tray
if "%choice%"=="3" goto setup_startup
if "%choice%"=="4" goto config_gui
if "%choice%"=="5" goto test_db
if "%choice%"=="6" goto status
if "%choice%"=="7" goto exit
echo Invalid choice. Please try again.
goto menu

:run_web
echo.
echo 🌐 Starting Label Print Server (Web Mode)...
echo Access the application at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
.\.venv\Scripts\python.exe app.py
goto menu

:run_tray
echo.
echo 🖥️ Starting Label Print Server (Tray Mode)...
echo The application will run in the system tray
echo Right-click the tray icon for options
echo.
.\.venv\Scripts\python.exe tray_app.py
goto menu

:setup_startup
echo.
echo 🚀 Setting up Auto-Startup...
.\.venv\Scripts\python.exe auto_startup.py install
if errorlevel 1 (
    echo ❌ Failed to setup auto-startup
) else (
    echo ✅ Auto-startup configured successfully
    echo The application will now start automatically when Windows boots
)
pause
goto menu

:config_gui
echo.
echo ⚙️ Opening Configuration GUI...
.\.venv\Scripts\python.exe tray_gui.py
goto menu

:test_db
echo.
echo 🗄️ Testing Database Connection...
.\.venv\Scripts\python.exe -c "
import sys
sys.path.append('.')
from app import get_party_info
try:
    # Test with a sample query
    result = get_party_info('test')
    if result is None:
        print('✅ Database connection successful (no data for test query)')
    else:
        print('✅ Database connection successful')
        print(f'Sample result: {result}')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    print('Please check your database configuration in db_settings.json')
"
pause
goto menu

:status
echo.
echo 📊 System Status Check
echo ========================================
echo.

echo 🐍 Python Environment:
.\.venv\Scripts\python.exe --version

echo.
echo 📦 Installed Packages:
.\.venv\Scripts\pip.exe list | findstr -i "flask pyodbc"

echo.
echo 🔄 Auto-Startup Status:
.\.venv\Scripts\python.exe auto_startup.py status

echo.
echo 📋 Update Status:
.\.venv\Scripts\python.exe update_manager.py status

echo.
echo 🗄️ Configuration Files:
if exist "db_settings.json" (
    echo   ✅ db_settings.json - Present
) else (
    echo   ❌ db_settings.json - Missing
)

if exist "VERSION" (
    echo   ✅ VERSION - Present
) else (
    echo   ❌ VERSION - Missing
)

if exist ".env" (
    echo   ✅ .env - Present
) else (
    echo   ℹ️ .env - Not found (optional)
)

echo.
pause
goto menu

:exit
echo.
echo ========================================
echo        Setup Complete!
echo ========================================
echo.
echo Quick Start Guide:
echo   • Web Mode: run setup.bat and choose option 1
echo   • Tray Mode: run setup.bat and choose option 2  
echo   • Auto-Start: Use option 3 to enable startup on boot
echo   • Configuration: Use option 4 to open settings GUI
echo.
echo Files Overview:
echo   • app.py - Main Flask application
echo   • tray_app.py - System tray version
echo   • setup.bat - This setup script
echo   • update_cli.bat - Update management CLI
echo.
echo For support, check README.md or API_DOCUMENTATION.md
echo.
pause