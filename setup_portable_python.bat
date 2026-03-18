@echo off
REM Setup portable Python using WinPython or Python.org installer

echo ============================================
echo Setting Up Portable Python
echo ============================================
echo.

set PYTHON_VERSION=3.9.13
set PYTHON_DIR=python_standalone
set DOWNLOAD_DIR=temp_download

REM Create directories
if exist "%PYTHON_DIR%" rmdir /s /q "%PYTHON_DIR%"
mkdir "%PYTHON_DIR%"
mkdir "%DOWNLOAD_DIR%"

echo Downloading Python %PYTHON_VERSION%...
set PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe
set INSTALLER=%DOWNLOAD_DIR%\python-installer.exe

powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%INSTALLER%'"

if not exist "%INSTALLER%" (
    echo ERROR: Download failed
    pause
    exit /b 1
)

echo.
echo Installing Python to portable directory...
echo This may take a few minutes...

REM Install Python to a specific directory
"%INSTALLER%" /quiet InstallAllUsers=0 TargetDir="%CD%\%PYTHON_DIR%" Include_pip=1 Include_test=0 Include_tcltk=1 Include_launcher=0 PrependPath=0 AssociateFiles=0

REM Wait for installation
timeout /t 30 /nobreak >nul

REM Check if installation succeeded
if not exist "%PYTHON_DIR%\python.exe" (
    echo ERROR: Installation failed - python.exe not found
    pause
    exit /b 1
)

echo.
echo Installing required packages...
"%PYTHON_DIR%\python.exe" -m pip install --upgrade pip
"%PYTHON_DIR%\python.exe" -m pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Package installation failed
    pause
    exit /b 1
)

echo.
echo Cleaning up...
rmdir /s /q "%DOWNLOAD_DIR%"

echo.
echo ============================================
echo Portable Python Setup Complete!
echo Location: %PYTHON_DIR%
echo Python: %PYTHON_DIR%\python.exe
echo Pythonw: %PYTHON_DIR%\pythonw.exe
echo ============================================
echo.
echo You can now build the installer
pause
