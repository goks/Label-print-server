@echo off
REM Update Manager CLI for Label Print Server

echo ========================================
echo    Label Print Server - Update Manager
echo ========================================
echo.

cd /d "%~dp0"

if "%1"=="" goto menu
if /i "%1"=="check" goto check
if /i "%1"=="install" goto install
if /i "%1"=="config" goto config
if /i "%1"=="status" goto status
goto usage

:menu
echo Select an option:
echo   1. Check for updates
echo   2. Install updates
echo   3. View configuration
echo   4. Show status
echo   5. Exit
echo.
set /p choice="Enter choice (1-5): "

if "%choice%"=="1" goto check
if "%choice%"=="2" goto install  
if "%choice%"=="3" goto config
if "%choice%"=="4" goto status
if "%choice%"=="5" goto exit
echo Invalid choice. Please try again.
goto menu

:check
echo.
echo 🔍 Checking for updates...
.\.venv\Scripts\python.exe update_manager.py check --force
pause
goto menu

:install
echo.
echo 📦 Installing updates...
.\.venv\Scripts\python.exe update_manager.py update
pause
goto menu

:config
echo.
echo ⚙️ Current Configuration:
.\.venv\Scripts\python.exe update_manager.py config
pause
goto menu

:status
echo.
echo 📊 Update Status:
.\.venv\Scripts\python.exe update_manager.py status
pause
goto menu

:usage
echo Usage: update_cli.bat [command]
echo Commands:
echo   check    - Check for updates
echo   install  - Install available updates
echo   config   - View configuration
echo   status   - Show current status
echo.
goto exit

:exit
echo.
echo Goodbye!