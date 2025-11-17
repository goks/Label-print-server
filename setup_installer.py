"""
Label Print Server - Setup Installer
One-click installation with Windows startup integration
"""

import os
import sys
import winreg
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import shutil
import json

class SetupInstaller:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Label Print Server - Setup")
        self.root.geometry("650x650")
        self.root.resizable(True, True)
        
        # Center window
        self.center_window()
        
        # Installation paths
        self.app_dir = Path(__file__).parent
        self.install_dir = Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')) / 'LabelPrintServer'
        self.startup_enabled = tk.BooleanVar(value=True)
        self.install_location = tk.StringVar(value=str(self.install_dir))
        
        self.setup_ui()
    
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        """Create the installation UI"""
        # Header
        header_frame = tk.Frame(self.root, bg='#2563eb', height=70)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        title = tk.Label(
            header_frame,
            text="📄 Label Print Server",
            font=('Arial', 18, 'bold'),
            bg='#2563eb',
            fg='white'
        )
        title.pack(pady=8)
        
        subtitle = tk.Label(
            header_frame,
            text="Setup & Installation Wizard",
            font=('Arial', 9),
            bg='#2563eb',
            fg='white'
        )
        subtitle.pack()
        
        # Main content with scrollbar
        canvas_frame = tk.Frame(self.root)
        canvas_frame.pack(fill='both', expand=True)
        
        canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient='vertical', command=canvas.yview)
        
        content_frame = tk.Frame(canvas, padx=30, pady=15)
        
        content_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=content_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Welcome message
        welcome = tk.Label(
            content_frame,
            text="Welcome to Label Print Server Setup",
            font=('Arial', 13, 'bold')
        )
        welcome.pack(pady=(0, 8))
        
        info = tk.Label(
            content_frame,
            text="This wizard will install Label Print Server on your computer.\n"
                 "The application will run as a system tray service.",
            justify='left',
            wraplength=550
        )
        info.pack(pady=(0, 15))
        
        # Installation location
        location_frame = tk.LabelFrame(content_frame, text="Installation Location", padx=10, pady=8)
        location_frame.pack(fill='x', pady=(0, 12))
        
        location_entry = tk.Entry(location_frame, textvariable=self.install_location, width=55)
        location_entry.pack(side='left', padx=(0, 5))
        
        browse_btn = tk.Button(location_frame, text="Browse...", command=self.browse_location)
        browse_btn.pack(side='left')
        
        # Options
        options_frame = tk.LabelFrame(content_frame, text="Installation Options", padx=10, pady=8)
        options_frame.pack(fill='x', pady=(0, 12))
        
        startup_check = tk.Checkbutton(
            options_frame,
            text="Start automatically when Windows starts",
            variable=self.startup_enabled,
            font=('Arial', 9)
        )
        startup_check.pack(anchor='w')
        
        # Features list
        features_frame = tk.LabelFrame(content_frame, text="Features", padx=10, pady=8)
        features_frame.pack(fill='x', pady=(0, 15))
        
        features = [
            "✅ System tray application",
            "✅ Auto-start on Windows boot",
            "✅ BarTender label printing integration",
            "✅ Web-based user interface",
            "✅ Database connectivity (SQL Server)",
            "✅ Automatic updates"
        ]
        
        for feature in features:
            tk.Label(features_frame, text=feature, anchor='w', font=('Arial', 9)).pack(anchor='w', pady=1)
        
        # Add some bottom padding to content frame
        tk.Frame(content_frame, height=20).pack()
        
        # Buttons
        button_frame = tk.Frame(self.root, padx=30, pady=15)
        button_frame.pack(fill='x', side='bottom')
        
        install_btn = tk.Button(
            button_frame,
            text="Install",
            command=self.install,
            bg='#2563eb',
            fg='white',
            font=('Arial', 11, 'bold'),
            width=15,
            height=2
        )
        install_btn.pack(side='right', padx=(5, 0))
        
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=self.root.quit,
            width=15,
            height=2
        )
        cancel_btn.pack(side='right')
    
    def browse_location(self):
        """Browse for installation directory"""
        directory = filedialog.askdirectory(
            title="Select Installation Directory",
            initialdir=str(self.install_dir.parent)
        )
        if directory:
            self.install_location.set(directory)
    
    def install(self):
        """Perform the installation"""
        install_path = Path(self.install_location.get())
        
        # Create progress window
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Installing...")
        progress_window.geometry("400x150")
        progress_window.resizable(False, False)
        
        # Center progress window
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() // 2) - 200
        y = (progress_window.winfo_screenheight() // 2) - 75
        progress_window.geometry(f'400x150+{x}+{y}')
        
        status_label = tk.Label(progress_window, text="Installing...", font=('Arial', 10))
        status_label.pack(pady=20)
        
        progress = ttk.Progressbar(progress_window, length=350, mode='indeterminate')
        progress.pack(pady=10)
        progress.start(10)
        
        def run_installation():
            try:
                # Step 1: Check prerequisites
                status_label.config(text="Checking prerequisites...")
                self.root.update()
                
                if not self.check_python():
                    raise Exception("Python virtual environment not found. Please ensure .venv exists.")
                
                # Step 2: Create installation directory
                status_label.config(text="Creating installation directory...")
                self.root.update()
                
                install_path.mkdir(parents=True, exist_ok=True)
                
                # Step 3: Copy files
                status_label.config(text="Copying application files...")
                self.root.update()
                
                self.copy_files(install_path)
                
                # Step 4: Create shortcuts
                status_label.config(text="Creating shortcuts...")
                self.root.update()
                
                self.create_shortcuts(install_path)
                
                # Step 5: Setup auto-start
                if self.startup_enabled.get():
                    status_label.config(text="Configuring auto-start...")
                    self.root.update()
                    
                    self.setup_autostart(install_path)
                
                # Step 6: Install dependencies (if needed)
                status_label.config(text="Finalizing installation...")
                self.root.update()
                
                # Save installation info
                self.save_install_info(install_path)
                
                progress.stop()
                progress_window.destroy()
                
                # Success message
                result = messagebox.askyesno(
                    "Installation Complete",
                    f"Label Print Server has been successfully installed to:\n{install_path}\n\n"
                    "The application is now running in your system tray.\n\n"
                    "Would you like to open the web interface now?",
                    icon='info'
                )
                
                if result:
                    import webbrowser
                    webbrowser.open("http://localhost:5000")
                
                # Start the tray app
                self.start_tray_app(install_path)
                
                self.root.quit()
                
            except Exception as e:
                progress.stop()
                progress_window.destroy()
                messagebox.showerror("Installation Failed", f"Installation failed:\n\n{str(e)}")
        
        # Run installation in thread to keep UI responsive
        import threading
        install_thread = threading.Thread(target=run_installation, daemon=True)
        install_thread.start()
    
    def check_python(self):
        """Check if Python virtual environment exists"""
        venv_python = self.app_dir / '.venv' / 'Scripts' / 'python.exe'
        return venv_python.exists()
    
    def copy_files(self, install_path):
        """Copy application files to installation directory"""
        # Files to copy
        files_to_copy = [
            'app.py',
            'tray_app.py',
            'tray_app_v2.py',
            'tray_gui.py',
            'printed_db.py',
            'update_manager.py',
            'wsgi.py',
            'requirements.txt',
            'VERSION',
            'README.md',
            'FUNCTIONS.md',
            'update_config.json',
            'db_settings.json',
            'startup_launcher.vbs'
        ]
        
        # Directories to copy
        dirs_to_copy = [
            'templates',
            'icons',
            'logs',
            '.venv'
        ]
        
        # Copy files
        for file_name in files_to_copy:
            src = self.app_dir / file_name
            if src.exists():
                dst = install_path / file_name
                shutil.copy2(src, dst)
        
        # Copy directories
        for dir_name in dirs_to_copy:
            src = self.app_dir / dir_name
            if src.exists():
                dst = install_path / dir_name
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
    
    def create_shortcuts(self, install_path):
        """Create desktop and start menu shortcuts"""
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            
            # Desktop shortcut
            desktop = Path(shell.SpecialFolders("Desktop"))
            shortcut_path = desktop / "Label Print Server.lnk"
            
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.TargetPath = str(install_path / '.venv' / 'Scripts' / 'pythonw.exe')
            shortcut.Arguments = f'"{install_path / "tray_app_v2.py"}"'
            shortcut.WorkingDirectory = str(install_path)
            shortcut.IconLocation = str(install_path / 'icons' / 'app_icon.ico')
            shortcut.Description = "Label Print Server"
            shortcut.save()
            
            # Start Menu shortcut
            start_menu = Path(shell.SpecialFolders("Programs"))
            start_menu_folder = start_menu / "Label Print Server"
            start_menu_folder.mkdir(exist_ok=True)
            
            shortcut_path = start_menu_folder / "Label Print Server.lnk"
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.TargetPath = str(install_path / '.venv' / 'Scripts' / 'pythonw.exe')
            shortcut.Arguments = f'"{install_path / "tray_app_v2.py"}"'
            shortcut.WorkingDirectory = str(install_path)
            shortcut.IconLocation = str(install_path / 'icons' / 'app_icon.ico')
            shortcut.Description = "Label Print Server"
            shortcut.save()
            
            # Uninstall shortcut
            shortcut_path = start_menu_folder / "Uninstall.lnk"
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.TargetPath = str(install_path / '.venv' / 'Scripts' / 'pythonw.exe')
            shortcut.Arguments = f'"{install_path / "uninstall.py"}"'
            shortcut.WorkingDirectory = str(install_path)
            shortcut.Description = "Uninstall Label Print Server"
            shortcut.save()
            
        except Exception as e:
            print(f"Warning: Could not create shortcuts: {e}")
    
    def setup_autostart(self, install_path):
        """Add application to Windows startup"""
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            
            # Use VBS launcher for reliable startup
            vbs_launcher = install_path / 'startup_launcher.vbs'
            
            value = f'wscript.exe "{vbs_launcher}"'
            winreg.SetValueEx(key, "LabelPrintServer", 0, winreg.REG_SZ, value)
            winreg.CloseKey(key)
            
            print("Auto-start configured successfully")
        except Exception as e:
            print(f"Warning: Could not setup auto-start: {e}")
    
    def save_install_info(self, install_path):
        """Save installation information"""
        info = {
            'install_path': str(install_path),
            'install_date': str(Path(__file__).stat().st_mtime),
            'version': self.get_version(),
            'auto_start': self.startup_enabled.get()
        }
        
        info_file = install_path / 'install_info.json'
        with open(info_file, 'w') as f:
            json.dump(info, f, indent=2)
        
        # Create uninstaller
        self.create_uninstaller(install_path)
    
    def get_version(self):
        """Get application version"""
        version_file = self.app_dir / 'VERSION'
        if version_file.exists():
            return version_file.read_text().strip()
        return "1.0.0"
    
    def create_uninstaller(self, install_path):
        """Create uninstaller script"""
        uninstall_script = '''"""
Label Print Server - Uninstaller
"""

import os
import sys
import winreg
import shutil
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

def remove_autostart():
    """Remove from Windows startup"""
    try:
        key_path = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, "LabelPrintServer")
        winreg.CloseKey(key)
    except:
        pass

def remove_shortcuts():
    """Remove shortcuts"""
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        
        # Desktop shortcut
        desktop = Path(shell.SpecialFolders("Desktop"))
        shortcut = desktop / "Label Print Server.lnk"
        if shortcut.exists():
            shortcut.unlink()
        
        # Start menu folder
        start_menu = Path(shell.SpecialFolders("Programs"))
        folder = start_menu / "Label Print Server"
        if folder.exists():
            shutil.rmtree(folder)
    except:
        pass

def main():
    root = tk.Tk()
    root.withdraw()
    
    response = messagebox.askyesno(
        "Uninstall Label Print Server",
        "Are you sure you want to uninstall Label Print Server?\\n\\n"
        "This will remove the application and all shortcuts.",
        icon='warning'
    )
    
    if not response:
        sys.exit(0)
    
    try:
        install_dir = Path(__file__).parent
        
        # Stop tray app if running
        lock_file = install_dir / '.tray_running'
        if lock_file.exists():
            messagebox.showwarning(
                "Application Running",
                "Please close Label Print Server from the system tray before uninstalling."
            )
            sys.exit(1)
        
        # Remove autostart
        remove_autostart()
        
        # Remove shortcuts
        remove_shortcuts()
        
        messagebox.showinfo(
            "Uninstall Complete",
            f"Label Print Server has been uninstalled.\\n\\n"
            f"You can manually delete the installation folder:\\n{install_dir}"
        )
        
        # Schedule deletion of install directory
        import subprocess
        subprocess.Popen(
            f'timeout /t 2 & rmdir /s /q "{install_dir}"',
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
    except Exception as e:
        messagebox.showerror("Uninstall Error", f"Error during uninstall:\\n{e}")

if __name__ == "__main__":
    main()
'''
        
        uninstall_file = install_path / 'uninstall.py'
        with open(uninstall_file, 'w') as f:
            f.write(uninstall_script)
    
    def start_tray_app(self, install_path):
        """Start the tray application"""
        try:
            pythonw = install_path / '.venv' / 'Scripts' / 'pythonw.exe'
            tray_app = install_path / 'tray_app_v2.py'
            
            subprocess.Popen(
                [str(pythonw), str(tray_app)],
                cwd=str(install_path),
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except Exception as e:
            print(f"Warning: Could not start tray app: {e}")
    
    def run(self):
        """Run the installer"""
        self.root.mainloop()

if __name__ == "__main__":
    # Check if running as administrator
    import ctypes
    if not ctypes.windll.shell32.IsUserAnAdmin():
        messagebox.showwarning(
            "Administrator Required",
            "This installer should be run as Administrator for best results.\n\n"
            "Right-click the installer and select 'Run as administrator'."
        )
    
    installer = SetupInstaller()
    installer.run()
