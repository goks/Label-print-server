import threading
import os
import sys
import webbrowser
import requests
import subprocess
from PIL import Image
import tkinter as tk
from tkinter import messagebox
import atexit
import tempfile
import json
import time
import logging

# Add win32 imports for custom tray icon
import win32api
import win32gui
import win32con
import win32gui_struct
import win32process
import win32event

# Add the current directory to the path so we can import app
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from waitress import serve
import signal

# Global variables
server_thread = None
server_running = False
server_stop_event = threading.Event()
waitress_server = None
window = None
status_label = None
hwnd = None
gui_proc = None

# Token file for local control requests from GUI process
CONTROL_TOKEN_FILE = os.path.join(os.path.dirname(__file__), '.tray_control_token')

# Single instance check
def check_single_instance():
    """Check if another instance is already running"""
    tray_running_file = os.path.join(os.path.dirname(__file__), '.tray_running')
    
    if os.path.exists(tray_running_file):
        try:
            with open(tray_running_file, 'r') as f:
                existing_pid = f.read().strip()
            
            # Check if the process with that PID is still running
            try:
                existing_pid = int(existing_pid)
                # Try to get process info (this will fail if process doesn't exist)
                if os.name == 'nt':  # Windows
                    import ctypes
                    handle = ctypes.windll.kernel32.OpenProcess(0x400, False, existing_pid)  # PROCESS_QUERY_INFORMATION
                    if handle:
                        ctypes.windll.kernel32.CloseHandle(handle)
                        return False  # Process exists, another instance is running
                else:
                    # For non-Windows (though this is a Windows app)
                    os.kill(existing_pid, 0)
                    return False  # Process exists
            except (OSError, ValueError):
                # Process doesn't exist, remove stale file
                print(f"Removing stale tray running file (PID {existing_pid} not found)")
                try:
                    os.remove(tray_running_file)
                except OSError as e:
                    print(f"Could not remove stale file: {e}")
                    # If we can't remove it, try to overwrite it anyway
                    pass
        except Exception as e:
            # Error reading file, assume it's stale
            print(f"Error reading tray running file: {e}")
            try:
                os.remove(tray_running_file)
            except OSError:
                pass
    
    return True  # No other instance running

def cleanup_tray():
    """Clean up tray icon and resources"""
    global hwnd
    try:
        if hwnd:
            win32gui.Shell_NotifyIcon(NIM_DELETE, (hwnd, TRAY_ICON_ID, 0, 0, 0, ""))
            print("Tray icon removed")
    except Exception as e:
        print(f"Error removing tray icon: {e}")

# Removed old mutex-based single instance check - using file-based approach now

# Tray icon constants
TRAY_ICON_ID = 1
WM_TRAYICON = 1024 + 1  # WM_USER + 1
NIF_ICON = 2
NIF_MESSAGE = 1
NIF_TIP = 4
NIM_ADD = 0
NIM_DELETE = 2

def update_status():
    global status_label
    if status_label and status_label.winfo_exists():
        status = "Running" if server_running else "Stopped"
        status_label.config(text=f"Server Status: {status}")

# Global flag to control the signal monitor
_monitor_running = True

def persistent_signal_monitor():
    """Persistent thread to monitor for start/stop/quit signals"""
    global _monitor_running, server_running
    
    print("Starting persistent signal monitor...")
    
    while _monitor_running:
        try:
            # Check for quit signal file (complete shutdown)
            quit_signal_file = os.path.join(os.path.dirname(__file__), '.tray_quit_signal')
            if os.path.exists(quit_signal_file):
                print("Quit signal detected, shutting down completely...")
                try:
                    os.remove(quit_signal_file)
                except Exception:
                    pass
                
                # Stop server if running
                if server_running:
                    server_stop_event.set()
                
                # Clean up tray running file and schedule complete exit
                def complete_exit():
                    time.sleep(1)  # Wait for server to stop
                    try:
                        tray_running_file = os.path.join(os.path.dirname(__file__), '.tray_running')
                        if os.path.exists(tray_running_file):
                            os.remove(tray_running_file)
                            print("Removed tray running indicator file")
                    except Exception as e:
                        print(f"Error removing tray running file: {e}")
                    print("Exiting tray application completely...")
                    os._exit(0)
                
                exit_thread = threading.Thread(target=complete_exit, daemon=True)
                exit_thread.start()
                break
            
            # Check for regular stop signal file
            stop_signal_file = os.path.join(os.path.dirname(__file__), '.tray_stop_signal')
            if os.path.exists(stop_signal_file) and server_running:
                print("Stop signal file detected, stopping server...")
                try:
                    os.remove(stop_signal_file)
                except Exception:
                    pass
                server_stop_event.set()
                
            # Check for start signal file (only if server not running)
            start_signal_file = os.path.join(os.path.dirname(__file__), '.tray_start_signal')
            if os.path.exists(start_signal_file) and not server_running:
                print("Start signal file detected, starting server...")
                try:
                    os.remove(start_signal_file)
                except Exception:
                    pass
                # Start the server in a separate thread
                threading.Thread(target=start_server, daemon=True).start()
                
        except Exception as e:
            print(f"Error in signal monitor: {e}")
            
        time.sleep(0.5)  # Check every 500ms
    
    print("Signal monitor stopped")

def setup_logging():
    """Configure logging to suppress waitress shutdown errors"""
    try:
        # Suppress waitress socket errors during shutdown
        waitress_logger = logging.getLogger('waitress')
        waitress_logger.setLevel(logging.CRITICAL)  # Only show critical errors
        
        # Create a custom handler that filters out socket errors
        class SocketErrorFilter(logging.Filter):
            def filter(self, record):
                message = record.getMessage()
                # Filter out common socket shutdown errors
                if any(error in message for error in [
                    "not a socket", 
                    "Bad file descriptor",
                    "An operation was attempted on something that is not a socket"
                ]):
                    return False
                return True
        
        # Apply filter to waitress logger
        for handler in waitress_logger.handlers:
            handler.addFilter(SocketErrorFilter())
            
    except Exception as e:
        print(f"Error setting up logging: {e}")

def run_server():
    global server_running, waitress_server
    
    print("Starting Flask server thread...")
    server_running = True
    server_stop_event.clear()
    
    # Setup logging to suppress waitress errors
    setup_logging()
    
    try:
        # Create waitress server with channel timeout and better cleanup settings
        from waitress.server import create_server
        waitress_server = create_server(
            app, 
            host='0.0.0.0', 
            port=5000, 
            threads=4, 
            channel_timeout=1,
            cleanup_interval=1,
            connection_limit=100
        )
        print("Server created, starting to listen...")
        
        # Run server in current thread with stop monitoring
        def check_stop_event():
            """Check stop event in a separate thread"""
            while server_running and not server_stop_event.is_set():
                time.sleep(0.1)
            
            if server_stop_event.is_set():
                print("Stop event detected, initiating server shutdown...")
                try:
                    waitress_server.close()
                except Exception as e:
                    print(f"Error during server.close(): {e}")
        
        # Start stop event monitor in daemon thread
        stop_monitor = threading.Thread(target=check_stop_event, daemon=True)
        stop_monitor.start()
        
        # Run server in current thread (blocking call)
        print("Server started, waiting for requests...")
        try:
            waitress_server.run()
        except Exception as e:
            # Suppress common shutdown errors
            if "not a socket" not in str(e) and "Bad file descriptor" not in str(e):
                print(f"Server runner error: {e}")
        
        print("Server run() method completed")
        
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        # Cleanup and reset state
        print("Server cleanup starting...")
        
        if waitress_server:
            try:
                print("Gracefully closing waitress server...")
                # Give pending requests time to complete
                time.sleep(0.3)
                waitress_server.close()
                # Wait a bit more for cleanup
                time.sleep(0.2)
            except Exception as e:
                print(f"Error closing server: {e}")
        
        # Reset the Flask app stop flag
        try:
            if hasattr(app, '_stop_requested'):
                app._stop_requested = False
                print("Reset Flask app stop flag")
        except Exception as e:
            print(f"Error resetting stop flag: {e}")
        
        # Reset global state
        server_running = False
        waitress_server = None
        print("Server cleanup completed - ready for restart")
        update_status()

def start_server():
    global server_thread, server_running
    
    print(f"start_server() called - current server_running: {server_running}")
    
    if server_running:
        print("Server already running, ignoring start request")
        return
        
    # Reset the stop flag in Flask app when starting
    try:
        if hasattr(app, '_stop_requested'):
            app._stop_requested = False
            print("Reset Flask app stop flag")
    except Exception as e:
        print(f"Error resetting stop flag: {e}")
    
    # Ensure control token exists for GUI to use
    try:
        with open(CONTROL_TOKEN_FILE, 'w') as f:
            f.write('control-token')
        print("Control token file created")
    except Exception as e:
        print(f"Error creating control token: {e}")

    # Create a brand new server thread
    print("Creating new server thread...")
    server_thread = threading.Thread(target=run_server, daemon=False)  # Not daemon so it can complete properly
    server_thread.start()
    print("Server thread started successfully")
    
    # Update status in main thread
    update_status()

def stop_server():
    global server_running, waitress_server, server_thread
    
    print(f"stop_server() called - current server_running: {server_running}")
    
    if not server_running:
        print("Server not running, ignoring stop request")
        return
    
    print("Setting stop event...")
    server_stop_event.set()
    
    # Also try to close the waitress server directly if available
    if waitress_server:
        try:
            print("Closing waitress server directly...")
            waitress_server.close()
        except Exception as e:
            print(f"Error closing waitress server: {e}")
    
    # Don't set server_running = False here - let run_server() cleanup do it
    # This prevents race conditions
    print("Server stop signal sent, waiting for cleanup...")
    update_status()

def restore_gui_via_signal():
    """Try to restore GUI using signal file method"""
    try:
        temp_dir = tempfile.gettempdir()
        restore_file = os.path.join(temp_dir, 'label_print_restore_signal.tmp')
        
        # Create signal file to tell GUI to restore itself
        with open(restore_file, 'w') as f:
            f.write('restore')
        
        print('Sent restore signal via file')
        
        # Wait a bit to see if restoration worked
        time.sleep(1.0)
        
        # Check if signal file was consumed (GUI removed it)
        consumed = not os.path.exists(restore_file)
        print(f'Signal file consumed: {consumed}')
        return consumed
        
    except Exception as e:
        print(f'Error sending restore signal: {e}')
        return False

def restore_gui_direct(target_pid):
    """Try direct window restoration via Win32 API"""
    try:
        found = False
        def enum_win(hwnd, extra):
            nonlocal found
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if pid == target_pid:
                    # Get window info
                    text = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    
                    # Look for our tkinter window
                    if class_name == "Tk" or "Label Print Server" in text:
                        print(f'Found window: {text} (class: {class_name}, visible: {win32gui.IsWindowVisible(hwnd)})')
                        try:
                            # Force show the window
                            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                            win32gui.SetForegroundWindow(hwnd)
                            found = True
                            print(f'Restored window successfully')
                            return False
                        except Exception as e:
                            print(f'Error restoring window: {e}')
            except Exception as e:
                print(f'Error in enum callback: {e}')
            return True

        win32gui.EnumWindows(enum_win, None)
        return found
        
    except Exception as e:
        print(f'Error in direct restore: {e}')
        return False

def show_gui(icon, item):
    """Launch or focus a separate GUI process. Guard against multiple launches."""
    global gui_proc
    try:
        gui_script = os.path.join(os.path.dirname(__file__), 'tray_gui.py')
        if not os.path.exists(gui_script):
            print('tray_gui.py not found; falling back to in-process GUI')
            create_window()
            return

        # Check if we already have a running GUI process
        if gui_proc is not None and gui_proc.poll() is None:
            print(f'GUI process {gui_proc.pid} is still running, attempting to restore...')
            
            # Try signal file method first
            restored = restore_gui_via_signal()
            
            if not restored:
                print('Signal method failed, trying direct window restoration...')
                restored = restore_gui_direct(gui_proc.pid)
            
            if restored:
                print('Successfully restored existing GUI window')
                return
            else:
                print('Could not restore GUI window - launching new one')
                # Kill the old unresponsive process
                try:
                    import psutil
                    proc = psutil.Process(gui_proc.pid)
                    proc.kill()
                    print(f'Killed unresponsive GUI process {gui_proc.pid}')
                except:
                    pass
                gui_proc = None

        # Clean up dead process reference
        if gui_proc is not None and gui_proc.poll() is not None:
            print(f'Previous GUI process {gui_proc.pid} has ended')
            gui_proc = None

        # Launch new GUI process using pythonw.exe (no console window)
        print('Launching new GUI process...')
        
        pythonw_exe = os.path.join(os.path.dirname(__file__), '.venv', 'Scripts', 'pythonw.exe')
        
        # Launch without console window
        gui_proc = subprocess.Popen(
            [pythonw_exe, gui_script],
            cwd=os.path.dirname(__file__),
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        print(f'Launched GUI process {gui_proc.pid}')
        
    except Exception as e:
        print(f'Failed to launch GUI process: {e}')
        import traceback
        traceback.print_exc()
        try:
            create_window()
        except Exception as e2:
            print(f'Fallback GUI failed: {e2}')

def create_window():
    global window, status_label
    if window is None or not window.winfo_exists():
        window = tk.Tk()
        window.title("Label Print Server")
        window.geometry("300x200")
        window.protocol("WM_DELETE_WINDOW", minimize_to_tray)

        # Status label
        status_label = tk.Label(window, text="Server Status: Checking...")
        status_label.pack(pady=10)

        # Buttons
        start_btn = tk.Button(window, text="Start Server", command=start_server)
        start_btn.pack(pady=5)

        stop_btn = tk.Button(window, text="Stop Server", command=stop_server)
        stop_btn.pack(pady=5)

        open_browser_btn = tk.Button(window, text="Open in Browser", command=open_in_browser)
        open_browser_btn.pack(pady=5)

        exit_btn = tk.Button(window, text="Exit", command=exit_app)
        exit_btn.pack(pady=5)

    update_status()
    window.deiconify()  # Show the window

def minimize_to_tray():
    if window:
        window.withdraw()

def open_in_browser():
    try:
        webbrowser.open("http://localhost:5000")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open browser: {e}")

def exit_app():
    stop_server()
    if window:
        window.destroy()
    if hwnd:
        win32gui.DestroyWindow(hwnd)

# Tray icon implementation using win32
TRAY_ICON_ID = 1
WM_TRAYICON = win32con.WM_USER + 1

def show_context_menu(hwnd):
    """Show context menu for tray icon"""
    try:
        # Create popup menu
        hmenu = win32gui.CreatePopupMenu()
        
        # Add menu items - using InsertMenu instead of AppendMenu for better compatibility  
        win32gui.InsertMenu(hmenu, 0, win32con.MF_BYPOSITION | win32con.MF_STRING, 1001, "Open in Browser")
        win32gui.InsertMenu(hmenu, 1, win32con.MF_BYPOSITION | win32con.MF_STRING, 1002, "Show Settings GUI")
        win32gui.InsertMenu(hmenu, 2, win32con.MF_BYPOSITION | win32con.MF_SEPARATOR, 0, None)
        
        # Server control
        if server_running:
            win32gui.InsertMenu(hmenu, 3, win32con.MF_BYPOSITION | win32con.MF_STRING, 1003, "Stop Server")
        else:
            win32gui.InsertMenu(hmenu, 3, win32con.MF_BYPOSITION | win32con.MF_STRING, 1004, "Start Server")
        
        win32gui.InsertMenu(hmenu, 4, win32con.MF_BYPOSITION | win32con.MF_SEPARATOR, 0, None)
        win32gui.InsertMenu(hmenu, 5, win32con.MF_BYPOSITION | win32con.MF_STRING, 1005, "Quit")
        
        # Get cursor position
        pos = win32gui.GetCursorPos()
        
        # Set foreground window (required for popup menu to work properly)
        win32gui.SetForegroundWindow(hwnd)
        
        # Show popup menu - create a zero RECT
        rect = (0, 0, 0, 0)
        cmd = win32gui.TrackPopupMenu(
            hmenu,
            win32con.TPM_LEFTALIGN | win32con.TPM_RETURNCMD,
            pos[0], pos[1], 0, hwnd, rect
        )
        
        # Handle menu selection
        if cmd == 1001:  # Open in Browser
            open_in_browser()
        elif cmd == 1002:  # Show Settings GUI
            show_gui(None, None)
        elif cmd == 1003:  # Stop Server
            stop_server()
        elif cmd == 1004:  # Start Server
            start_server()
        elif cmd == 1005:  # Quit
            quit_application()
        
        # Clean up
        win32gui.DestroyMenu(hmenu)
        
        # Post message to clear menu state
        win32gui.PostMessage(hwnd, win32con.WM_NULL, 0, 0)
        
    except Exception as e:
        print(f"Error showing context menu: {e}")
        # Fallback to opening browser
        open_in_browser()

def quit_application():
    """Quit the entire application including server"""
    try:
        print("Quit requested from tray menu...")
        
        # Create quit signal file
        quit_signal_file = os.path.join(os.path.dirname(__file__), '.tray_quit_signal')
        with open(quit_signal_file, 'w') as f:
            f.write('quit')
        
        # Exit after a short delay to allow signal processing
        def delayed_exit():
            time.sleep(0.5)
            os._exit(0)
        
        exit_thread = threading.Thread(target=delayed_exit, daemon=True)
        exit_thread.start()
        
    except Exception as e:
        print(f"Error during quit: {e}")
        os._exit(0)

def wnd_proc(hwnd, msg, wparam, lparam):
    # Debug: print incoming messages for troubleshooting
    # try:
    #     print(f"wnd_proc: msg={msg}, lparam={lparam}, wparam={wparam}")
    # except Exception:
    #     pass

    if msg == WM_TRAYICON:
        # Handle left clicks and double-clicks to show GUI
        if lparam in (win32con.WM_LBUTTONDBLCLK, win32con.WM_LBUTTONDOWN, win32con.WM_LBUTTONUP):
            show_gui(None, None)
        # Handle right click to show context menu
        elif lparam == win32con.WM_RBUTTONUP:
            show_context_menu(hwnd)
    elif msg == win32con.WM_DESTROY:
        win32gui.PostQuitMessage(0)
    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

# Check for single instance
if not check_single_instance():
    # Another instance is already running
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    
    response = messagebox.askyesno(
        "Label Print Server", 
        "Another instance of Label Print Server may be running.\n\n"
        "This could be a stale process or control file.\n\n"
        "Do you want to force start anyway?\n"
        "(This will clean up old files and processes)",
        icon='warning'
    )
    
    if response:
        # User chose to force start - clean up
        print("User chose to force start - cleaning up...")
        tray_running_file = os.path.join(os.path.dirname(__file__), '.tray_running')
        try:
            if os.path.exists(tray_running_file):
                os.remove(tray_running_file)
                print("Removed stale tray running file")
        except Exception as e:
            print(f"Error removing file: {e}")
            messagebox.showerror("Error", f"Could not remove stale file: {e}\n\nPlease run cleanup_tray.bat")
            root.destroy()
            sys.exit(1)
        # Continue with startup
    else:
        # User chose not to force start
        print("User cancelled startup")
        root.destroy()
        sys.exit(0)
    
    root.destroy()

# Create window class
wc = win32gui.WNDCLASS()
wc.lpfnWndProc = wnd_proc
wc.hInstance = win32api.GetModuleHandle(None)
wc.lpszClassName = "TrayApp"
wc.hIcon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
wc.hCursor = win32api.LoadCursor(0, win32con.IDC_ARROW)

# Register class
class_atom = win32gui.RegisterClass(wc)

# Create window
hwnd = win32gui.CreateWindow(class_atom, "TrayApp", 0, 0, 0, 0, 0, 0, 0, win32api.GetModuleHandle(None), None)

# Load icon (try loading ICO file; fall back to default app icon on any failure)
icon_paths = [
    os.path.join(os.path.dirname(__file__), "icons", "app_icon.ico"),
    os.path.join(os.path.dirname(__file__), "icons", "favicon.ico")
]

hicon = None
for icon_path in icon_paths:
    if os.path.exists(icon_path):
        try:
            hicon = win32gui.LoadImage(0, icon_path, win32con.IMAGE_ICON, 16, 16, win32con.LR_LOADFROMFILE)
            if hicon:
                print(f"Loaded tray icon from: {icon_path}")
                break
        except Exception as e:
            print(f"Warning: LoadImage failed for {icon_path}: {e}")

if not hicon:
    hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
    print("Using default system icon for tray")

# Add tray icon
nid = (hwnd, TRAY_ICON_ID, NIF_ICON | NIF_MESSAGE | NIF_TIP, WM_TRAYICON, hicon, "Label Print Server")
win32gui.Shell_NotifyIcon(NIM_ADD, nid)

# Cleanup function for atexit
def cleanup_on_exit():
    """Clean up tray files on exit"""
    try:
        tray_running_file = os.path.join(os.path.dirname(__file__), '.tray_running')
        if os.path.exists(tray_running_file):
            os.remove(tray_running_file)
            print("Cleaned up tray running file on exit")
    except Exception as e:
        print(f"Error cleaning up on exit: {e}")

# Register cleanup function
atexit.register(cleanup_on_exit)

# Create tray running indicator file
try:
    tray_running_file = os.path.join(os.path.dirname(__file__), '.tray_running')
    with open(tray_running_file, 'w') as f:
        f.write(str(os.getpid()))
    print("Created tray running indicator file")
except Exception as e:
    print(f"Error creating tray running file: {e}")

# Start server
start_server()

# Start persistent signal monitor
monitor_thread = threading.Thread(target=persistent_signal_monitor, daemon=True)
monitor_thread.start()

# Message loop
win32gui.PumpMessages()

# Cleanup
print("Tray app shutting down...")
try:
    tray_running_file = os.path.join(os.path.dirname(__file__), '.tray_running')
    if os.path.exists(tray_running_file):
        os.remove(tray_running_file)
        print("Removed tray running indicator file")
except Exception as e:
    print(f"Error removing tray running file: {e}")

win32gui.Shell_NotifyIcon(NIM_DELETE, (hwnd, TRAY_ICON_ID, 0, 0, 0, ""))