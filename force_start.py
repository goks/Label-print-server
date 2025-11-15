#!/usr/bin/env python3
"""
Force Start Utility for Label Print Server
Kills all processes, cleans up files, and starts fresh
"""

import os
import sys
import time
import subprocess
import psutil

APP_DIR = os.path.dirname(os.path.abspath(__file__))

def kill_all_processes():
    """Kill all Label Print Server Python processes"""
    killed = 0
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            exe = proc.info['exe']
            if exe and 'Label-print-server' in exe and 'python' in proc.info['name'].lower():
                print(f"Killing process {proc.info['pid']} - {proc.info['name']}")
                proc.kill()
                killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return killed

def cleanup_files():
    """Remove all control files"""
    cleaned = 0
    patterns = ['.tray_running', '.tray_control_token', '.tray_stop_signal', 
                '.tray_start_signal', '.tray_quit_signal']
    
    for pattern in patterns:
        filepath = os.path.join(APP_DIR, pattern)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"Removed {pattern}")
                cleaned += 1
            except Exception as e:
                print(f"Error removing {pattern}: {e}")
    
    return cleaned

def start_tray_app():
    """Start the tray application"""
    pythonw = os.path.join(APP_DIR, '.venv', 'Scripts', 'pythonw.exe')
    tray_script = os.path.join(APP_DIR, 'tray_app.py')
    
    if not os.path.exists(pythonw):
        print(f"Error: Python executable not found at {pythonw}")
        return False
    
    try:
        subprocess.Popen([pythonw, tray_script], 
                        cwd=APP_DIR,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, 'CREATE_NEW_PROCESS_GROUP') else 0)
        return True
    except Exception as e:
        print(f"Error starting tray app: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Label Print Server - Force Start Utility")
    print("=" * 50)
    print()
    
    print("[1/3] Killing existing processes...")
    killed = kill_all_processes()
    print(f"  Killed {killed} process(es)")
    
    print("\n[2/3] Cleaning up control files...")
    cleaned = cleanup_files()
    print(f"  Removed {cleaned} file(s)")
    
    print("\n[3/3] Starting tray application...")
    time.sleep(1)  # Give processes time to fully terminate
    
    if start_tray_app():
        print("  ✓ Tray app started successfully!")
        print("\nCheck your system tray for the Label Print Server icon.")
    else:
        print("  ✗ Failed to start tray app")
        print("\nPlease check the logs for errors.")
    
    print("\n" + "=" * 50)
    input("\nPress Enter to exit...")
