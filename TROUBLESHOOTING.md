# Troubleshooting Guide - Label Print Server

## Common Issues and Solutions

### 🔴 "Another instance is already running"

**Problem:** When trying to run the tray app, you get a message saying another instance is running.

**Cause:** The previous tray app didn't clean up properly, leaving stale control files.

**Solution:**
```batch
# Option 1: Run the cleanup script
cleanup_tray.bat

# Option 2: Manual cleanup (PowerShell)
Remove-Item ".tray_running" -Force
Remove-Item ".tray_control_token" -Force

# Option 3: Delete files manually
# Delete these files from the application folder:
# - .tray_running
# - .tray_control_token
# - .tray_stop_signal
# - .tray_start_signal
# - .tray_quit_signal
```

**Prevention:** The app now has better cleanup handling and should remove these files automatically on exit.

---

### 🔴 Server Won't Start

**Problem:** The Flask server doesn't start when clicking "Start Server"

**Solution:**
1. Check if port 5000 is already in use:
   ```powershell
   netstat -ano | findstr :5000
   ```
2. If port is in use, kill the process:
   ```powershell
   taskkill /PID <process_id> /F
   ```
3. Check the logs in `logs/` directory for errors

---

### 🔴 Database Connection Failed

**Problem:** Cannot connect to SQL Server database

**Solution:**
1. Verify database settings in `db_settings.json`
2. Ensure SQL Server is running
3. Check Windows Authentication is enabled
4. Test connection:
   ```batch
   complete_setup.bat
   # Choose option 5: Test Database Connection
   ```

---

### 🔴 Print Jobs Not Working

**Problem:** Labels aren't printing when pressing Enter

**Solution:**
1. Check if default printer is set in Windows
2. Verify print command in PowerShell:
   ```powershell
   Get-Printer | Where-Object {$_.Default -eq $true}
   ```
3. Check async print processing is enabled in `app.py`
4. Review logs for print errors

---

### 🔴 Update Check Fails

**Problem:** Cannot check for updates or update system errors

**Solution:**
1. Check internet connection
2. Verify GitHub repository URL in update config
3. Check if GitHub API rate limit exceeded:
   ```batch
   update_cli.bat status
   ```
4. Force update check:
   ```batch
   update_cli.bat check
   ```

---

### 🔴 GUI Won't Show

**Problem:** Clicking the tray icon doesn't show the GUI

**Solution:**
1. Check if GUI process is running:
   ```powershell
   Get-Process | Where-Object {$_.ProcessName -like "*python*"}
   ```
2. Try running GUI directly:
   ```batch
   .venv\Scripts\python.exe tray_gui.py
   ```
3. Check for errors in console output
4. Restart the tray app completely

---

### 🔴 Auto-Startup Not Working

**Problem:** Application doesn't start when Windows boots

**Solution:**
1. Check registry entry:
   ```batch
   .venv\Scripts\python.exe auto_startup.py status
   ```
2. Re-enable auto-startup:
   ```batch
   .venv\Scripts\python.exe auto_startup.py install
   ```
3. Verify VBS script exists: `start_tray_silent.vbs`
4. Check Windows Event Viewer for startup errors

---

## System Reset

If all else fails, perform a complete system reset:

```batch
# 1. Stop all running instances
taskkill /F /IM python.exe

# 2. Clean up all control files
cleanup_tray.bat

# 3. Remove auto-startup
.venv\Scripts\python.exe auto_startup.py uninstall

# 4. Reinstall dependencies
setup.bat

# 5. Reconfigure system
complete_setup.bat
```

---

## Getting Diagnostic Information

### Collect Logs
```batch
# Copy all logs to desktop
xcopy logs\*.* "%USERPROFILE%\Desktop\label-print-logs\" /E /I
```

### System Status
```batch
# Complete system check
complete_setup.bat
# Choose option 6: Check System Status
```

### Process Information
```powershell
# List all Python processes
Get-Process python | Format-Table Id, ProcessName, StartTime, Path -AutoSize

# Check port usage
netstat -ano | findstr "5000"
```

---

## Contact Support

When reporting issues, please include:
- Error messages from logs
- System status output
- Windows version
- Python version
- Steps to reproduce

Check these files for detailed logs:
- `logs/label_print_server.log` - Application logs
- `logs/database.log` - Database operations
- `logs/access.log` - Web requests
- Console output from tray app
