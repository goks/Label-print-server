@echo off
REM Cleanup script for Label Print Server tray files
REM Use this if the tray app says "another instance is already running"

cd /d "%~dp0"

echo Cleaning up tray control files...

if exist ".tray_running" (
    del /f /q ".tray_running"
    echo   ✓ Removed .tray_running
)

if exist ".tray_control_token" (
    del /f /q ".tray_control_token"
    echo   ✓ Removed .tray_control_token
)

if exist ".tray_stop_signal" (
    del /f /q ".tray_stop_signal"
    echo   ✓ Removed .tray_stop_signal
)

if exist ".gui_running" (
    del /f /q ".gui_running"
    echo   ✓ Removed .gui_running
)

if exist ".tray_start_signal" (
    del /f /q ".tray_start_signal"
    echo   ✓ Removed .tray_start_signal
)

if exist ".tray_quit_signal" (
    del /f /q ".tray_quit_signal"
    echo   ✓ Removed .tray_quit_signal
)

echo.
echo Cleanup complete! You can now run the tray app.
echo.
pause
