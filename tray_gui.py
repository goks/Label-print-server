import tkinter as tk
from tkinter import messagebox
import webbrowser
import requests
import os
import sys

# Simple standalone GUI for controlling the Label Print Server
class TrayGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Label Print Server")
        self.geometry("300x200")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.status_label = tk.Label(self, text="Server Status: Checking...")
        self.status_label.pack(pady=10)

        start_btn = tk.Button(self, text="Start Server", command=self.start_server)
        start_btn.pack(pady=5)

        stop_btn = tk.Button(self, text="Stop Server", command=self.stop_server)
        stop_btn.pack(pady=5)

        open_browser_btn = tk.Button(self, text="Open in Browser", command=self.open_browser)
        open_browser_btn.pack(pady=5)

        exit_btn = tk.Button(self, text="Exit", command=self.on_close)
        exit_btn.pack(pady=5)

        self.after(1000, self.update_status)

    def update_status(self):
        try:
            r = requests.get('http://localhost:5000/get-settings', timeout=1)
            running = r.status_code == 200
        except Exception:
            running = False
        status = "Running" if running else "Stopped"
        self.status_label.config(text=f"Server Status: {status}")
        self.after(2000, self.update_status)

    def start_server(self):
        # Starting is handled by the tray process; attempt to call endpoint to start if present
        try:
            # No start endpoint; inform user to start tray process
            messagebox.showinfo("Info", "Server is started by tray process automatically.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def stop_server(self):
        try:
            # Read token file created by tray_app
            token_file = os.path.join(os.path.dirname(__file__), '.tray_control_token')
            token = None
            if os.path.exists(token_file):
                try:
                    with open(token_file, 'r') as f:
                        token = f.read().strip()
                except Exception:
                    token = None

            payload = {'action': 'stop', 'token': token}
            r = requests.post('http://127.0.0.1:5000/control', json=payload, timeout=3)
            if r.status_code == 200:
                messagebox.showinfo('Info', 'Server stop requested')
            else:
                messagebox.showerror('Error', f'Control endpoint error: {r.status_code} {r.text}')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop server: {e}")

    def open_browser(self):
        webbrowser.open('http://localhost:5000')

    def on_close(self):
        self.destroy()

if __name__ == '__main__':
    app = TrayGUI()
    app.mainloop()
