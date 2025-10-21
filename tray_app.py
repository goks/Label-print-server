import threading
import os
import sys
import webbrowser
import requests
import subprocess
from PIL import Image
import tkinter as tk
from tkinter import messagebox

# Add win32 imports for custom tray icon
import win32api
import win32gui
import win32con
import win32gui_struct

# Add the current directory to the path so we can import app
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from waitress import serve

# Global variables
server_thread = None
server_running = False
window = None
status_label = None
hwnd = None
gui_proc = None

# Token file for local control requests from GUI process
CONTROL_TOKEN_FILE = os.path.join(os.path.dirname(__file__), '.tray_control_token')

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

def run_server():
    global server_running
    server_running = True
    try:
        # Run using waitress; it'll block this thread until stopped via the stop_event
        serve(app, host='0.0.0.0', port=5000, threads=4)
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        server_running = False
        update_status()

def start_server():
    global server_thread, server_running
    if not server_running:
        # ensure control token exists for GUI to use
        with open(CONTROL_TOKEN_FILE, 'w') as f:
            f.write('control-token')

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        update_status()

def stop_server():
    global server_running
    if server_running:
        # Signal the server to stop by requesting the internal control endpoint
        try:
            if os.path.exists(CONTROL_TOKEN_FILE):
                token = open(CONTROL_TOKEN_FILE).read().strip()
            else:
                token = 'control-token'

            r = requests.post('http://127.0.0.1:5000/control', json={'action': 'stop', 'token': token}, timeout=3)
            print('stop_server: control response', r.status_code, r.text)
        except Exception as e:
            print(f"Error stopping server via control endpoint: {e}")
        # waitress doesn't expose a shutdown on the served function; rely on the control endpoint in app.py to call os._exit
        server_running = False
        update_status()

def show_gui(icon, item):
    """Launch or focus a separate GUI process. Guard against multiple launches."""
    global gui_proc
    try:
        gui_script = os.path.join(os.path.dirname(__file__), 'tray_gui.py')
        if not os.path.exists(gui_script):
            print('tray_gui.py not found; falling back to in-process GUI')
            create_window()
            return

        # If gui_proc is alive, do nothing (or try to bring it to front)
        if gui_proc and gui_proc.poll() is None:
            print('GUI already running')
            return

        # Launch GUI process with token file path argument
        gui_proc = subprocess.Popen([sys.executable, gui_script], close_fds=True)
        print('Launched GUI process', gui_proc.pid)
    except Exception as e:
        print(f'Failed to launch GUI process: {e}')
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

def wnd_proc(hwnd, msg, wparam, lparam):
    # Debug: print incoming messages for troubleshooting
    try:
        print(f"wnd_proc: msg={msg}, lparam={lparam}, wparam={wparam}")
    except Exception:
        pass

    if msg == WM_TRAYICON:
        # log specific lparam values
        if lparam in (win32con.WM_LBUTTONDBLCLK, win32con.WM_RBUTTONUP):
            print(f"tray event: dblclick or rbuttonup received (lparam={lparam})")
            show_gui(None, None)
        # also respond to single left click (down/up) and right button down
        elif lparam in (win32con.WM_LBUTTONDOWN, win32con.WM_LBUTTONUP, win32con.WM_RBUTTONDOWN):
            print(f"tray event: click received (lparam={lparam})")
            show_gui(None, None)
    elif msg == win32con.WM_DESTROY:
        win32gui.PostQuitMessage(0)
    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

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
icon_path = os.path.join(os.path.dirname(__file__), "icons", "favicon.ico")
hicon = None
if os.path.exists(icon_path):
    try:
        hicon = win32gui.LoadImage(0, icon_path, win32con.IMAGE_ICON, 16, 16, win32con.LR_LOADFROMFILE)
    except Exception as e:
        print(f"Warning: LoadImage failed for {icon_path}: {e}")
        hicon = None

if not hicon:
    hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

# Add tray icon
nid = (hwnd, TRAY_ICON_ID, NIF_ICON | NIF_MESSAGE | NIF_TIP, WM_TRAYICON, hicon, "Label Print Server")
win32gui.Shell_NotifyIcon(NIM_ADD, nid)

# Start server
start_server()

# Message loop
win32gui.PumpMessages()

# Cleanup
win32gui.Shell_NotifyIcon(NIM_DELETE, (hwnd, TRAY_ICON_ID, 0, 0, 0, ""))