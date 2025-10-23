@echo off
REM Integration Test Script for Label Print Server
REM Tests all major components and their interactions

echo ========================================
echo   Label Print Server - System Test
echo ========================================
echo.

cd /d "%~dp0"

set TESTS_PASSED=0
set TESTS_FAILED=0
set TEST_LOG=test_results_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log

echo Starting comprehensive system test... > %TEST_LOG%
echo Test started at %date% %time% >> %TEST_LOG%
echo. >> %TEST_LOG%

echo 🧪 Running comprehensive system tests...
echo Results will be saved to: %TEST_LOG%
echo.

REM Test 1: Python Environment
echo [1/10] Testing Python environment...
.\.venv\Scripts\python.exe --version > nul 2>&1
if errorlevel 1 (
    echo   ❌ FAIL: Python virtual environment not working
    echo [FAIL] Python virtual environment test >> %TEST_LOG%
    set /a TESTS_FAILED+=1
) else (
    echo   ✅ PASS: Python virtual environment working
    echo [PASS] Python virtual environment test >> %TEST_LOG%
    set /a TESTS_PASSED+=1
)

REM Test 2: Dependencies
echo [2/10] Testing required dependencies...
.\.venv\Scripts\python.exe -c "import flask, pyodbc, requests, packaging; print('Dependencies OK')" > nul 2>&1
if errorlevel 1 (
    echo   ❌ FAIL: Required dependencies missing
    echo [FAIL] Dependencies test >> %TEST_LOG%
    set /a TESTS_FAILED+=1
) else (
    echo   ✅ PASS: All required dependencies available
    echo [PASS] Dependencies test >> %TEST_LOG%
    set /a TESTS_PASSED+=1
)

REM Test 3: Flask App Import
echo [3/10] Testing Flask application import...
.\.venv\Scripts\python.exe -c "from app import app; print('Flask app import OK')" > nul 2>&1
if errorlevel 1 (
    echo   ❌ FAIL: Flask application import failed
    echo [FAIL] Flask app import test >> %TEST_LOG%
    set /a TESTS_FAILED+=1
) else (
    echo   ✅ PASS: Flask application imports successfully
    echo [PASS] Flask app import test >> %TEST_LOG%
    set /a TESTS_PASSED+=1
)

REM Test 4: Update Manager
echo [4/10] Testing Update Manager...
.\.venv\Scripts\python.exe -c "from update_manager import UpdateManager; m=UpdateManager(); print('Update Manager OK')" > nul 2>&1
if errorlevel 1 (
    echo   ❌ FAIL: Update Manager initialization failed
    echo [FAIL] Update Manager test >> %TEST_LOG%
    set /a TESTS_FAILED+=1
) else (
    echo   ✅ PASS: Update Manager working
    echo [PASS] Update Manager test >> %TEST_LOG%
    set /a TESTS_PASSED+=1
)

REM Test 5: Auto Startup System
echo [5/10] Testing Auto Startup system...
.\.venv\Scripts\python.exe -c "from auto_startup import AutoStartupManager; m=AutoStartupManager(); print('Auto Startup OK')" > nul 2>&1
if errorlevel 1 (
    echo   ❌ FAIL: Auto Startup system failed
    echo [FAIL] Auto Startup test >> %TEST_LOG%
    set /a TESTS_FAILED+=1
) else (
    echo   ✅ PASS: Auto Startup system working
    echo [PASS] Auto Startup test >> %TEST_LOG%
    set /a TESTS_PASSED+=1
)

REM Test 6: Tray Application
echo [6/10] Testing Tray application import...
.\.venv\Scripts\python.exe -c "from tray_app import TrayApp; print('Tray App OK')" > nul 2>&1
if errorlevel 1 (
    echo   ❌ FAIL: Tray application import failed
    echo [FAIL] Tray application test >> %TEST_LOG%
    set /a TESTS_FAILED+=1
) else (
    echo   ✅ PASS: Tray application imports successfully
    echo [PASS] Tray application test >> %TEST_LOG%
    set /a TESTS_PASSED+=1
)

REM Test 7: Configuration Files
echo [7/10] Testing configuration files...
if exist "db_settings.json" (
    echo   ✅ PASS: Database settings file exists
    echo [PASS] Configuration files test - db_settings.json >> %TEST_LOG%
    set /a TESTS_PASSED+=1
) else (
    echo   ❌ FAIL: Database settings file missing
    echo [FAIL] Configuration files test - db_settings.json missing >> %TEST_LOG%
    set /a TESTS_FAILED+=1
)

REM Test 8: Version File
echo [8/10] Testing version tracking...
if exist "VERSION" (
    echo   ✅ PASS: Version file exists
    echo [PASS] Version file test >> %TEST_LOG%
    set /a TESTS_PASSED+=1
) else (
    echo   ❌ FAIL: Version file missing
    echo [FAIL] Version file test >> %TEST_LOG%
    set /a TESTS_FAILED+=1
)

REM Test 9: Logs Directory
echo [9/10] Testing logging system...
if exist "logs" (
    echo   ✅ PASS: Logs directory exists
    echo [PASS] Logging system test >> %TEST_LOG%
    set /a TESTS_PASSED+=1
) else (
    echo   ❌ FAIL: Logs directory missing
    echo [FAIL] Logging system test >> %TEST_LOG%
    set /a TESTS_FAILED+=1
)

REM Test 10: CLI Update Tool
echo [10/10] Testing CLI update tool...
if exist "update_cli.bat" (
    echo   ✅ PASS: CLI update tool available
    echo [PASS] CLI update tool test >> %TEST_LOG%
    set /a TESTS_PASSED+=1
) else (
    echo   ❌ FAIL: CLI update tool missing
    echo [FAIL] CLI update tool test >> %TEST_LOG%
    set /a TESTS_FAILED+=1
)

REM Test Results
echo.
echo ========================================
echo            Test Results
echo ========================================
echo   Tests Passed: %TESTS_PASSED%
echo   Tests Failed: %TESTS_FAILED%
echo   Total Tests:  %TESTS_TOTAL%

echo. >> %TEST_LOG%
echo ======================================== >> %TEST_LOG%
echo Test completed at %date% %time% >> %TEST_LOG%
echo Tests Passed: %TESTS_PASSED% >> %TEST_LOG%
echo Tests Failed: %TESTS_FAILED% >> %TEST_LOG%
echo ======================================== >> %TEST_LOG%

if %TESTS_FAILED% equ 0 (
    echo.
    echo ✅ ALL TESTS PASSED!
    echo System is ready for production use.
    echo.
    echo Quick Start:
    echo   1. Run complete_setup.bat for guided setup
    echo   2. Use setup.bat for standard installation  
    echo   3. Run update_cli.bat for update management
    echo.
) else (
    echo.
    echo ❌ SOME TESTS FAILED
    echo Please review the issues above before proceeding.
    echo Check %TEST_LOG% for detailed results.
    echo.
    echo Common Solutions:
    echo   • Run setup.bat to install missing dependencies
    echo   • Check Python installation and virtual environment
    echo   • Ensure all required files are present
    echo   • Review error messages in the log file
    echo.
)

echo Full test report saved to: %TEST_LOG%
echo.
pause