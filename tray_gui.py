import tkinter as tk
from tkinter import messagebox, font
import tkinter.ttk as ttk
import webbrowser
import requests
import os
import sys
import json
import tempfile
import winreg
import threading
from update_manager import UpdateManager


# Modern GUI for controlling the Label Print Server
class TrayGUI(tk.Tk):
    def set_app_user_model_id(self):
        """Set Application User Model ID to help Windows identify our app"""
        try:
            import ctypes
            from ctypes import wintypes, windll
            
            # Set a unique AppUserModelID
            app_id = "LabelPrintServer.TrayGUI.1.0"
            
            # Use SetCurrentProcessExplicitAppUserModelID
            shell32 = windll.shell32
            shell32.SetCurrentProcessExplicitAppUserModelID.argtypes = [wintypes.LPCWSTR]
            
            hr = shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            if hr == 0:  # S_OK
                print(f"Successfully set AppUserModelID: {app_id}")
                return True
            else:
                print(f"Failed to set AppUserModelID: {hr}")
                return False
        except Exception as e:
            print(f"Error setting AppUserModelID: {e}")
            return False

    def __init__(self):
        super().__init__()
        
        # Set AppUserModelID FIRST to help Windows identify our app
        self.set_app_user_model_id()
        
        # Set icon BEFORE setting other window properties
        self.setup_window_icon()
        
        self.title("📄 Label Print Server")
        self.geometry("900x550")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.configure(bg='#f0f0f0')  # Light gray background
        
        # Bind events to detect minimize
        self.bind('<Map>', self.on_map)
        self.bind('<Unmap>', self.on_unmap)
        self.is_mapped = True
        
        # Configure modern styling
        self.setup_modern_style()
        
        # Save window handle for tray restoration
        self.save_window_info()
        
        # Start checking for restore signals
        self.after(1000, self.check_restore_signal)
        
        # Create the modern interface
        self.create_modern_interface()

    def setup_modern_style(self):
        """Configure modern ttk styling"""
        style = ttk.Style()
        
        # Use a theme that supports color changes
        try:
            style.theme_use('clam')  # More customizable than default
        except:
            pass
        
        # Configure modern button style
        style.configure('Modern.TButton',
                       background='#e9ecef',
                       foreground='#495057',
                       borderwidth=1,
                       relief='solid',
                       padding=(12, 8),
                       focuscolor='none')
        
        style.map('Modern.TButton',
                  background=[('active', '#dee2e6'),
                             ('pressed', '#ced4da')])
        
        # Configure status button styles
        style.configure('Success.TButton',
                       background='#28a745',
                       foreground='white',
                       borderwidth=1,
                       relief='solid',
                       padding=(12, 8),
                       focuscolor='none')
        
        style.map('Success.TButton',
                  background=[('active', '#218838'),
                             ('pressed', '#1e7e34')])
        
        style.configure('Danger.TButton',
                       background='#dc3545',
                       foreground='white',
                       borderwidth=1,
                       relief='solid',
                       padding=(12, 8),
                       focuscolor='none')
        
        style.map('Danger.TButton',
                  background=[('active', '#c82333'),
                             ('pressed', '#bd2130')])
        
        style.configure('Primary.TButton',
                       background='#007bff',
                       foreground='white',
                       borderwidth=1,
                       relief='solid',
                       padding=(12, 8),
                       focuscolor='none')
        
        style.map('Primary.TButton',
                  background=[('active', '#0069d9'),
                             ('pressed', '#0062cc')])
        
        style.configure('Secondary.TButton',
                       background='#6c757d',
                       foreground='white',
                       borderwidth=1,
                       relief='solid',
                       padding=(8, 6),
                       focuscolor='none')
        
        style.map('Secondary.TButton',
                  background=[('active', '#5a6268'),
                             ('pressed', '#545b62')])
        
        # Configure treeview style
        style.configure('Modern.Treeview',
                       background='white',
                       foreground='#333333',
                       fieldbackground='white',
                       borderwidth=1,
                       relief='solid')
        
        style.configure('Modern.Treeview.Heading',
                       background='#f8f9fa',
                       foreground='#495057',
                       borderwidth=1,
                       relief='solid',
                       font=('Arial', 9, 'bold'))
        
        # Ensure proper text contrast for all states
        style.map('Modern.Treeview',
                  foreground=[('selected', 'white')],
                  background=[('selected', '#007bff')])

    def setup_window_icon(self):
        """Set window and taskbar icon if available"""
        try:
            # Try the new optimized ICO file first, then fallback to favicon.ico
            icon_paths = [
                os.path.join(os.path.dirname(__file__), "icons", "app_icon.ico"),
                os.path.join(os.path.dirname(__file__), "icons", "favicon.ico")
            ]
            
            icon_path = None
            for path in icon_paths:
                if os.path.exists(path):
                    icon_path = path
                    break
            
            if icon_path:
                print(f"Using icon file: {icon_path}")
                
                # Method 1: Try custom window class approach first
                try:
                    self.setup_custom_window_class(icon_path)
                except Exception as e:
                    print(f"Custom window class failed: {e}")
                
                # Method 2: Set window icon using multiple tkinter methods
                try:
                    self.iconbitmap(icon_path)
                    print(f"Set window icon via iconbitmap: {icon_path}")
                except Exception as e:
                    print(f"iconbitmap failed: {e}")
                
                try:
                    self.wm_iconbitmap(icon_path)
                    print(f"Set window icon via wm_iconbitmap: {icon_path}")
                except Exception as e:
                    print(f"wm_iconbitmap failed: {e}")
                
                # Method 3: Try PIL-based icon if available
                try:
                    self.set_pil_icon(icon_path)
                except Exception as e:
                    print(f"PIL icon method failed: {e}")
                
                # Schedule aggressive taskbar icon setting after window is fully created
                self.after(50, lambda: self.set_taskbar_icon(icon_path))
                self.after(200, lambda: self.set_taskbar_icon(icon_path))
                self.after(1000, lambda: self.set_taskbar_icon(icon_path))
                self.after(2000, lambda: self.set_taskbar_icon(icon_path))
            else:
                print("No icon files found")
        except Exception as e:
            print(f"Could not set window icon: {e}")
    
    def setup_custom_window_class(self, icon_path):
        """Try to set up a custom window class with icon"""
        try:
            import win32gui
            import win32con
            import win32api
            
            # This is experimental - try to change the window class after creation
            hwnd = self.winfo_id()
            if hwnd:
                # Load the icon
                hicon = win32gui.LoadImage(0, icon_path, win32con.IMAGE_ICON, 32, 32, win32con.LR_LOADFROMFILE)
                if hicon:
                    # Try to set the class icon directly
                    try:
                        win32api.SetClassLong(hwnd, win32con.GCL_HICON, hicon)
                        print(f"Set custom window class icon: {hicon}")
                    except Exception as e:
                        print(f"SetClassLong for custom class failed: {e}")
        except Exception as e:
            print(f"Custom window class setup failed: {e}")
    
    def set_pil_icon(self, icon_path):
        """Try using PIL to load and set icon"""
        try:
            from PIL import Image, ImageTk
            
            # Load image and convert to PhotoImage
            with Image.open(icon_path) as img:
                # Create different sizes
                sizes = [(16, 16), (32, 32)]
                for size in sizes:
                    resized = img.resize(size, Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(resized)
                    
                    # Try to set as window icon
                    try:
                        self.iconphoto(True, photo)
                        print(f"Set icon via PIL iconphoto: {size}")
                        # Keep a reference to prevent garbage collection
                        if not hasattr(self, '_icon_photos'):
                            self._icon_photos = []
                        self._icon_photos.append(photo)
                        break
                    except Exception as e:
                        print(f"PIL iconphoto failed for {size}: {e}")
        except Exception as e:
            print(f"PIL icon method failed: {e}")
    
    def set_taskbar_icon(self, icon_path):
        """Set taskbar icon using Win32 API with multiple methods"""
        try:
            import win32gui
            import win32con
            import win32api
            
            # Method 1: Get window handle using tkinter's winfo_id
            try:
                hwnd = self.winfo_id()
                if hwnd:
                    self._apply_taskbar_icon(hwnd, icon_path)
                    return
            except Exception as e:
                print(f"Method 1 failed: {e}")
            
            # Method 2: Find window by title
            try:
                hwnd = win32gui.FindWindow(None, self.title())
                if hwnd:
                    self._apply_taskbar_icon(hwnd, icon_path)
                    return
            except Exception as e:
                print(f"Method 2 failed: {e}")
                
            # Method 3: Enumerate windows to find ours
            try:
                current_pid = os.getpid()
                def enum_windows_proc(hwnd, lParam):
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        if pid == current_pid and win32gui.IsWindowVisible(hwnd):
                            window_text = win32gui.GetWindowText(hwnd)
                            if "Label Print Server" in window_text:
                                self._apply_taskbar_icon(hwnd, icon_path)
                                return False  # Stop enumeration
                    except Exception:
                        pass
                    return True
                
                import win32process
                win32gui.EnumWindows(enum_windows_proc, None)
            except Exception as e:
                print(f"Method 3 failed: {e}")
                
        except ImportError:
            print("Win32 modules not available for taskbar icon setting")
        except Exception as e:
            print(f"Could not set taskbar icon: {e}")
    
    def _apply_taskbar_icon(self, hwnd, icon_path):
        """Apply icon to window handle using multiple aggressive methods"""
        try:
            import win32gui
            import win32con
            import win32api
            import ctypes
            from ctypes import wintypes
            
            print(f"Attempting aggressive taskbar icon setting for window {hwnd}")
            
            # Method 1: Load multiple icon sizes
            icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
            icons = {}
            
            for width, height in icon_sizes:
                try:
                    hicon = win32gui.LoadImage(0, icon_path, win32con.IMAGE_ICON, width, height, win32con.LR_LOADFROMFILE)
                    if hicon:
                        icons[f"{width}x{height}"] = hicon
                        print(f"Loaded {width}x{height} icon: {hicon}")
                except Exception as e:
                    print(f"Failed to load {width}x{height} icon: {e}")
            
            # Method 2: Set window icons using multiple approaches
            if icons:
                # Use 16x16 for small icon, 32x32 for large icon
                small_icon = icons.get("16x16") or list(icons.values())[0]
                large_icon = icons.get("32x32") or icons.get("48x48") or list(icons.values())[0]
                
                # Set via SendMessage
                try:
                    result1 = win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, small_icon)
                    result2 = win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG, large_icon)
                    print(f"SendMessage results: ICON_SMALL={result1}, ICON_BIG={result2}")
                except Exception as e:
                    print(f"SendMessage failed: {e}")
                
                # Set via class properties (more persistent)
                try:
                    win32api.SetClassLongPtr(hwnd, win32con.GCL_HICON, large_icon)
                    win32api.SetClassLongPtr(hwnd, win32con.GCL_HICONSM, small_icon)
                    print("Set class icons via SetClassLongPtr")
                except AttributeError:
                    try:
                        win32api.SetClassLong(hwnd, win32con.GCL_HICON, large_icon)
                        win32api.SetClassLong(hwnd, win32con.GCL_HICONSM, small_icon)
                        print("Set class icons via SetClassLong")
                    except Exception as e:
                        print(f"SetClassLong failed: {e}")
                except Exception as e:
                    print(f"SetClassLongPtr failed: {e}")
            
            # Method 3: Force taskbar refresh using multiple techniques
            try:
                # Technique 1: Hide and show window to force taskbar update
                win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                print("Forced window hide/show cycle")
                
                # Technique 2: Redraw window
                win32gui.RedrawWindow(hwnd, None, None, 
                                    win32con.RDW_FRAME | win32con.RDW_INVALIDATE | win32con.RDW_UPDATENOW)
                print("Forced window redraw")
                
                # Technique 3: Notify shell of changes
                try:
                    # SHChangeNotify to refresh shell
                    shell32 = ctypes.windll.shell32
                    shell32.SHChangeNotify(0x8000000, 0x1000, None, None)  # SHCNE_ASSOCCHANGED, SHCNF_FLUSH
                    print("Notified shell of association changes")
                except Exception as e:
                    print(f"Shell notification failed: {e}")
                
            except Exception as e:
                print(f"Force refresh techniques failed: {e}")
            
            # Method 4: Alternative approach using ctypes directly
            try:
                user32 = ctypes.windll.user32
                
                # Define constants
                WM_SETICON = 0x0080
                ICON_SMALL = 0
                ICON_BIG = 1
                
                if icons:
                    small_icon = icons.get("16x16") or list(icons.values())[0]
                    large_icon = icons.get("32x32") or list(icons.values())[0]
                    
                    # Direct ctypes call
                    result1 = user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, small_icon)
                    result2 = user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, large_icon)
                    print(f"Direct ctypes results: SMALL={result1}, BIG={result2}")
            except Exception as e:
                print(f"Direct ctypes approach failed: {e}")
                
        except Exception as e:
            print(f"Error in aggressive taskbar icon setting: {e}")

    def create_modern_interface(self):
        """Create the modern interface with icons and better styling"""
        # Main container with padding
        main_container = tk.Frame(self, bg='#f0f0f0')
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header section with title and status
        self.create_header_section(main_container)
        
        # Control buttons section
        self.create_control_section(main_container)
        
        # Startup management section
        self.create_startup_section(main_container)
        
        # Update management section
        self.create_update_section(main_container)
        
        # Search and filters section
        self.create_search_section(main_container)
        
        # Data table section
        self.create_table_section(main_container)
        
        # Footer with pagination and actions
        self.create_footer_section(main_container)

    def create_header_section(self, parent):
        """Create header with title and status indicator"""
        header_frame = tk.Frame(parent, bg='#f0f0f0')
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Title with icon
        title_frame = tk.Frame(header_frame, bg='#f0f0f0')
        title_frame.pack(side='left')
        
        title_font = font.Font(size=16, weight='bold')
        title_label = tk.Label(title_frame, text="📄 Label Print Server", 
                              font=title_font, bg='#f0f0f0', fg='#333')
        title_label.pack(side='left')
        
        # Status indicator
        status_frame = tk.Frame(header_frame, bg='#f0f0f0')
        status_frame.pack(side='right')
        
        self.status_indicator = tk.Label(status_frame, text="●", font=('Arial', 20), 
                                       bg='#f0f0f0', fg='#ffc107')  # Yellow dot
        self.status_indicator.pack(side='right', padx=(0, 10))
        
        self.status_label = tk.Label(status_frame, text="Server Status: Checking...", 
                                   font=('Arial', 11, 'bold'), bg='#f0f0f0', fg='#666')
        self.status_label.pack(side='right')

    def create_control_section(self, parent):
        """Create control buttons with icons and tooltips"""
        control_frame = tk.Frame(parent, bg='#ffffff', relief='solid', bd=1)
        control_frame.pack(fill='x', pady=(0, 20), ipady=15)
        
        # Left side - Server controls
        left_controls = tk.Frame(control_frame, bg='#ffffff')
        left_controls.pack(side='left', padx=20)
        
        self.start_btn = self.create_modern_button(left_controls, "▶️ Start Server", 
                                                  self.start_server, 'success')
        self.start_btn.pack(side='left', padx=(0, 10))
        self.create_tooltip(self.start_btn, "Start the Label Print Server")
        
        self.stop_btn = self.create_modern_button(left_controls, "⏹️ Stop Server", 
                                                 self.stop_server, 'danger')
        self.stop_btn.pack(side='left', padx=(0, 10))
        self.create_tooltip(self.stop_btn, "Stop the Label Print Server")
        
        open_browser_btn = self.create_modern_button(left_controls, "🌐 Open Browser", 
                                                    self.open_browser, 'primary')
        open_browser_btn.pack(side='left')
        self.create_tooltip(open_browser_btn, "Open the web interface in your browser")
        
        # Right side - Window controls
        right_controls = tk.Frame(control_frame, bg='#ffffff')
        right_controls.pack(side='right', padx=20)
        
        self.minimize_btn = self.create_modern_button(right_controls, "➖ Minimize", 
                                                     self.minimize_to_tray, 'secondary')
        self.minimize_btn.pack(side='right', padx=(10, 0))
        self.create_tooltip(self.minimize_btn, "Minimize to system tray")
        
        self.quit_btn = self.create_modern_button(right_controls, "❌ Quit", 
                                                 self.quit_requested, 'secondary')
        self.quit_btn.pack(side='right')
        self.create_tooltip(self.quit_btn, "Quit the application")

    def create_startup_section(self, parent):
        """Create startup management section with status and controls"""
        startup_frame = tk.Frame(parent, bg='#ffffff', relief='solid', bd=1)
        startup_frame.pack(fill='x', pady=(0, 20), ipady=10)
        
        # Left side - Status display
        status_frame = tk.Frame(startup_frame, bg='#ffffff')
        status_frame.pack(side='left', padx=20)
        
        # Startup status label
        startup_label = tk.Label(status_frame, text="🚀 Auto-Startup:", 
                                font=('Arial', 10, 'bold'), bg='#ffffff', fg='#495057')
        startup_label.pack(side='left')
        
        # Status indicator
        self.startup_status_label = tk.Label(status_frame, text="Checking...", 
                                            font=('Arial', 10), bg='#ffffff', fg='#666')
        self.startup_status_label.pack(side='left', padx=(10, 0))
        
        # Right side - Control buttons
        controls_frame = tk.Frame(startup_frame, bg='#ffffff')
        controls_frame.pack(side='right', padx=20)
        
        self.enable_startup_btn = self.create_modern_button(controls_frame, "✅ Enable Auto-Startup", 
                                                           self.enable_startup, 'success')
        self.enable_startup_btn.pack(side='right', padx=(10, 0))
        self.create_tooltip(self.enable_startup_btn, "Configure app to start automatically with Windows")
        
        self.disable_startup_btn = self.create_modern_button(controls_frame, "❌ Disable Auto-Startup", 
                                                            self.disable_startup, 'danger')
        self.disable_startup_btn.pack(side='right')
        self.create_tooltip(self.disable_startup_btn, "Remove app from Windows startup")
        
        # Check startup status immediately
        self.check_startup_status()

    def check_startup_status(self):
        """Check if the application is configured for auto-startup"""
        try:
            startup_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            app_name = "Label Print Server"
            
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, startup_key, 0, winreg.KEY_READ) as key:
                try:
                    value, reg_type = winreg.QueryValueEx(key, app_name)
                    self.startup_status_label.config(text="✅ Enabled", fg='#28a745')
                    self.enable_startup_btn.config(state='disabled')
                    self.disable_startup_btn.config(state='normal')
                    return True
                except FileNotFoundError:
                    self.startup_status_label.config(text="❌ Disabled", fg='#dc3545')
                    self.enable_startup_btn.config(state='normal')
                    self.disable_startup_btn.config(state='disabled')
                    return False
        except Exception as e:
            self.startup_status_label.config(text="❓ Error", fg='#ffc107')
            print(f"Error checking startup status: {e}")
            return False

    def enable_startup(self):
        """Enable auto-startup configuration"""
        try:
            # Get the path to the silent startup script
            app_dir = os.path.dirname(os.path.abspath(__file__))
            vbs_file = os.path.join(app_dir, "start_tray_silent.vbs")
            
            if not os.path.exists(vbs_file):
                messagebox.showerror("Error", 
                    "start_tray_silent.vbs not found!\n"
                    "Please ensure all startup files are present.")
                return
            
            startup_command = f'wscript.exe "{vbs_file}"'
            startup_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            app_name = "Label Print Server"
            
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, startup_key, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, startup_command)
            
            messagebox.showinfo("Success", 
                "Auto-startup enabled successfully!\n\n"
                "The Label Print Server will now start automatically when Windows boots.\n"
                "The tray icon will appear in the system tray.")
            
            self.check_startup_status()  # Refresh status
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to enable auto-startup:\n{str(e)}")

    def disable_startup(self):
        """Disable auto-startup configuration"""
        try:
            startup_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            app_name = "Label Print Server"
            
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, startup_key, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, app_name)
            
            messagebox.showinfo("Success", 
                "Auto-startup disabled successfully!\n\n"
                "The Label Print Server will no longer start automatically with Windows.\n"
                "You can still start it manually using the desktop shortcut or this GUI.")
            
            self.check_startup_status()  # Refresh status
            
        except FileNotFoundError:
            messagebox.showinfo("Info", "Auto-startup was not configured.")
            self.check_startup_status()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to disable auto-startup:\n{str(e)}")

    def create_update_section(self, parent):
        """Create update management section with version info and update controls"""
        update_frame = tk.Frame(parent, bg='#ffffff', relief='solid', bd=1)
        update_frame.pack(fill='x', pady=(0, 20), ipady=10)
        
        # Left side - Version and update status
        status_frame = tk.Frame(update_frame, bg='#ffffff')
        status_frame.pack(side='left', padx=20)
        
        # Version info
        version_label = tk.Label(status_frame, text="📦 Version:", 
                                font=('Arial', 10, 'bold'), bg='#ffffff', fg='#495057')
        version_label.pack(side='left')
        
        self.version_label = tk.Label(status_frame, text="Loading...", 
                                     font=('Arial', 10), bg='#ffffff', fg='#666')
        self.version_label.pack(side='left', padx=(10, 20))
        
        # Update status
        update_status_label = tk.Label(status_frame, text="🔄 Updates:", 
                                      font=('Arial', 10, 'bold'), bg='#ffffff', fg='#495057')
        update_status_label.pack(side='left')
        
        self.update_status_label = tk.Label(status_frame, text="Checking...", 
                                           font=('Arial', 10), bg='#ffffff', fg='#666')
        self.update_status_label.pack(side='left', padx=(10, 0))
        
        # Right side - Control buttons
        controls_frame = tk.Frame(update_frame, bg='#ffffff')
        controls_frame.pack(side='right', padx=20)
        
        self.check_updates_btn = self.create_modern_button(controls_frame, "🔍 Check Updates", 
                                                          self.check_for_updates, 'primary')
        self.check_updates_btn.pack(side='right', padx=(10, 0))
        self.create_tooltip(self.check_updates_btn, "Check GitHub for available updates")
        
        self.install_update_btn = self.create_modern_button(controls_frame, "📥 Install Update", 
                                                           self.install_update, 'success')
        self.install_update_btn.pack(side='right', padx=(10, 0))
        self.create_tooltip(self.install_update_btn, "Install available update")
        self.install_update_btn.config(state='disabled')  # Disabled until update is available
        
        # Initialize update manager and get current version
        self.update_manager = None
        self.available_update = None
        self.initialize_update_system()

    def initialize_update_system(self):
        """Initialize the update management system"""
        try:
            self.update_manager = UpdateManager()
            current_version = self.update_manager.current_version
            self.version_label.config(text=f"v{current_version}")
            
            # Check for updates in background
            self.after(2000, self.check_for_updates_background)
            
        except Exception as e:
            self.version_label.config(text="Unknown")
            self.update_status_label.config(text="❌ Error", fg='#dc3545')
            print(f"Failed to initialize update system: {e}")

    def check_for_updates_background(self):
        """Check for updates in background without blocking UI"""
        def background_check():
            try:
                if self.update_manager:
                    result = self.update_manager.check_and_update(force=False)
                    
                    # Update UI in main thread
                    self.after(0, lambda: self.update_status_display(result))
            except Exception as e:
                self.after(0, lambda: self.update_status_display({'status': 'error', 'message': str(e)}))
        
        # Run in background thread
        threading.Thread(target=background_check, daemon=True).start()

    def update_status_display(self, result):
        """Update the UI with check results"""
        try:
            if result['status'] == 'no_update':
                self.update_status_label.config(text="✅ Up to date", fg='#28a745')
                self.install_update_btn.config(state='disabled')
                self.available_update = None
                
            elif result['status'] == 'update_available':
                version = result.get('version', 'Unknown')
                self.update_status_label.config(text=f"📦 v{version} available", fg='#007bff')
                self.install_update_btn.config(state='normal')
                self.available_update = result
                
            elif result['status'] == 'updated':
                version = result.get('version', 'Unknown')
                self.update_status_label.config(text=f"✅ Updated to v{version}", fg='#28a745')
                self.install_update_btn.config(state='disabled')
                self.available_update = None
                
            elif result['status'] == 'error':
                self.update_status_label.config(text="❌ Check failed", fg='#dc3545')
                self.install_update_btn.config(state='disabled')
                
        except Exception as e:
            print(f"Error updating status display: {e}")

    def check_for_updates(self):
        """Manually check for updates"""
        self.update_status_label.config(text="🔄 Checking...", fg='#ffc107')
        self.check_updates_btn.config(state='disabled')
        
        def background_check():
            try:
                if self.update_manager:
                    result = self.update_manager.check_and_update(force=True)
                    self.after(0, lambda: self.update_status_display(result))
                else:
                    self.after(0, lambda: self.update_status_display({'status': 'error', 'message': 'Update system not initialized'}))
            except Exception as e:
                self.after(0, lambda: self.update_status_display({'status': 'error', 'message': str(e)}))
            finally:
                self.after(0, lambda: self.check_updates_btn.config(state='normal'))
        
        threading.Thread(target=background_check, daemon=True).start()

    def install_update(self):
        """Install available update"""
        if not self.available_update:
            messagebox.showwarning("No Update", "No update is currently available.")
            return
        
        version = self.available_update.get('version', 'Unknown')
        changelog = self.available_update.get('changelog', 'No changelog available.')
        
        # Show confirmation dialog
        message = f"Install update to version {version}?\n\n"
        if changelog:
            # Limit changelog length for dialog
            if len(changelog) > 300:
                changelog = changelog[:300] + "..."
            message += f"Changes:\n{changelog}\n\n"
        message += "⚠️ The application will restart after update."
        
        if not messagebox.askyesno("Install Update", message):
            return
        
        # Disable buttons and show progress
        self.install_update_btn.config(state='disabled')
        self.check_updates_btn.config(state='disabled')
        self.update_status_label.config(text="📥 Installing...", fg='#ffc107')
        
        def background_install():
            try:
                if self.update_manager:
                    result = self.update_manager.manual_update()
                    self.after(0, lambda: self.installation_complete(result))
                else:
                    self.after(0, lambda: self.installation_complete({'status': 'error', 'message': 'Update system not initialized'}))
            except Exception as e:
                self.after(0, lambda: self.installation_complete({'status': 'error', 'message': str(e)}))
        
        threading.Thread(target=background_install, daemon=True).start()

    def installation_complete(self, result):
        """Handle installation completion"""
        try:
            if result['status'] == 'success':
                version = result.get('version', 'Unknown')
                messagebox.showinfo("Update Complete", 
                    f"Successfully updated to version {version}!\n\n"
                    "The application will restart now.")
                
                # Restart the application
                self.restart_application()
                
            else:
                error_msg = result.get('message', 'Unknown error occurred')
                messagebox.showerror("Update Failed", 
                    f"Failed to install update:\n{error_msg}\n\n"
                    "Please try again or install manually.")
                
                # Re-enable buttons
                self.install_update_btn.config(state='normal')
                self.check_updates_btn.config(state='normal')
                self.update_status_label.config(text="❌ Install failed", fg='#dc3545')
                
        except Exception as e:
            print(f"Error handling installation completion: {e}")

    def restart_application(self):
        """Restart the application after update"""
        try:
            # Signal tray app to restart
            restart_signal_file = os.path.join(os.path.dirname(__file__), '.restart_required')
            with open(restart_signal_file, 'w') as f:
                f.write('update_complete')
            
            # Close GUI
            self.quit_requested()
            
        except Exception as e:
            print(f"Error restarting application: {e}")

    def create_modern_button(self, parent, text, command, button_type='default', **kwargs):
        """Create a modern button with proper styling and contrast"""
        # Define button styles with good contrast
        button_styles = {
            'success': {'bg': '#28a745', 'fg': 'white', 'activebackground': '#218838', 'activeforeground': 'white'},
            'danger': {'bg': '#dc3545', 'fg': 'white', 'activebackground': '#c82333', 'activeforeground': 'white'},
            'primary': {'bg': '#007bff', 'fg': 'white', 'activebackground': '#0069d9', 'activeforeground': 'white'},
            'secondary': {'bg': '#6c757d', 'fg': 'white', 'activebackground': '#5a6268', 'activeforeground': 'white'},
            'default': {'bg': '#e9ecef', 'fg': '#495057', 'activebackground': '#dee2e6', 'activeforeground': '#495057'}
        }
        
        style = button_styles.get(button_type, button_styles['default'])
        
        button = tk.Button(parent, text=text, command=command,
                          font=('Arial', 9, 'bold'),
                          relief='solid',
                          bd=1,
                          padx=12,
                          pady=8,
                          cursor='hand2',
                          **style,
                          **kwargs)
        
        return button
    
    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        tooltip = None
        
        def show_tooltip(event):
            nonlocal tooltip
            if tooltip:
                return  # Tooltip already visible
                
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            tooltip.configure(bg='#333333')
            
            label = tk.Label(tooltip, text=text, 
                           bg='#333333', fg='white', 
                           font=('Arial', 9), 
                           padx=5, pady=3)
            label.pack()
            
            # Auto-hide tooltip after 2 seconds as backup
            tooltip.after(2000, hide_tooltip)
        
        def hide_tooltip(event=None):
            nonlocal tooltip
            if tooltip:
                try:
                    tooltip.destroy()
                except:
                    pass
                tooltip = None
        
        # Show tooltip on mouse enter
        widget.bind('<Enter>', show_tooltip)
        # Hide tooltip on mouse leave
        widget.bind('<Leave>', hide_tooltip)

    def create_search_section(self, parent):
        """Create search and filter controls"""
        search_container = tk.Frame(parent, bg='#ffffff', relief='solid', bd=1)
        search_container.pack(fill='x', pady=(0, 20), ipady=10)
        
        search_frame = tk.Frame(search_container, bg='#ffffff')
        search_frame.pack(fill='x', padx=20)
        
        # Search label with icon
        search_label = tk.Label(search_frame, text="🔍 Search Quotation:", 
                               font=('Arial', 10, 'bold'), bg='#ffffff', fg='#666')
        search_label.pack(side='left')
        
        # Modern search entry
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, 
                               font=('Arial', 10), width=25, relief='solid', bd=1)
        search_entry.pack(side='left', padx=(10, 20))
        
        # Debounced dynamic search while typing
        self._search_after_id = None
        def on_key_release(event=None):
            if self._search_after_id:
                try:
                    self.after_cancel(self._search_after_id)
                except Exception:
                    pass
            self.current_page = 1
            self._search_after_id = self.after(400, lambda: self.reload_table(query=self.search_var.get().strip(), page=self.current_page))
        
        search_entry.bind('<KeyRelease>', on_key_release)
        
        # Action buttons
        search_btn = self.create_modern_button(search_frame, "🔍 Search", 
                                              self.on_search, 'default')
        search_btn.pack(side='left', padx=(0, 10))
        
        reload_btn = self.create_modern_button(search_frame, "🔄 Reload", 
                                              lambda: self.reload_table(query=self.search_var.get().strip(), page=self.current_page),
                                              'default')
        reload_btn.pack(side='left')

    def create_table_section(self, parent):
        """Create the data table with modern styling"""
        table_container = tk.Frame(parent, bg='#ffffff', relief='solid', bd=1)
        table_container.pack(fill='both', expand=True, pady=(0, 20))
        
        # Table header
        table_header = tk.Frame(table_container, bg='#f8f9fa', height=30)
        table_header.pack(fill='x', padx=1, pady=(1, 0))
        
        header_label = tk.Label(table_header, text="📊 Recent Print Records", 
                               font=('Arial', 11, 'bold'), bg='#f8f9fa', fg='#495057')
        header_label.pack(side='left', padx=15, pady=5)
        
        # Table with scrollbars
        table_frame = tk.Frame(table_container, bg='white')
        table_frame.pack(fill='both', expand=True, padx=1, pady=(0, 1))
        
        # Show printed_at immediately after id for readability
        cols = ('id','printed_at','quotation','party','address','phone','mobile')
        
        self.tree = ttk.Treeview(table_frame, columns=cols, show='headings', style='Modern.Treeview')
        
        # Configure column headings with icons
        self.tree.heading('id', text='🆔 ID')
        self.tree.heading('printed_at', text='📅 Date/Time')
        self.tree.heading('quotation', text='📝 Quotation')
        self.tree.heading('party', text='👤 Customer')
        self.tree.heading('address', text='📍 Address')
        self.tree.heading('phone', text='📞 Phone')
        self.tree.heading('mobile', text='📱 Mobile')
        
        # Configure column widths
        self.tree.column('id', width=60, minwidth=50)
        self.tree.column('printed_at', width=130, minwidth=120)
        self.tree.column('quotation', width=100, minwidth=80)
        self.tree.column('party', width=150, minwidth=100)
        self.tree.column('address', width=200, minwidth=150)
        self.tree.column('phone', width=100, minwidth=80)
        self.tree.column('mobile', width=100, minwidth=80)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack table and scrollbars
        self.tree.pack(side='left', fill='both', expand=True)
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')
        
        # Initialize pagination
        self.current_page = 1
        self.page_size = 50

    def create_footer_section(self, parent):
        """Create footer with pagination and export controls"""
        footer_frame = tk.Frame(parent, bg='#ffffff', relief='solid', bd=1)
        footer_frame.pack(fill='x', ipady=10)
        
        # Left side - Pagination controls
        pagination_frame = tk.Frame(footer_frame, bg='#ffffff')
        pagination_frame.pack(side='left', padx=20)
        
        self.prev_btn = self.create_modern_button(pagination_frame, "◀️ Previous", 
                                                  self.on_prev, 'default')
        self.prev_btn.pack(side='left', padx=(0, 10))
        
        self.page_label = tk.Label(pagination_frame, text='Page 1', 
                                  font=('Arial', 10, 'bold'), bg='#ffffff', fg='#666')
        self.page_label.pack(side='left', padx=(0, 10))
        
        self.next_btn = self.create_modern_button(pagination_frame, "Next ▶️", 
                                                 self.on_next, 'default')
        self.next_btn.pack(side='left')
        
        # Right side - Export controls
        export_frame = tk.Frame(footer_frame, bg='#ffffff')
        export_frame.pack(side='right', padx=20)
        
        copy_btn = self.create_modern_button(export_frame, "📋 Copy Selected", 
                                            self.copy_selected, 'default')
        copy_btn.pack(side='right', padx=(10, 0))
        
        export_btn = self.create_modern_button(export_frame, "📊 Export CSV", 
                                              self.export_csv, 'default')
        export_btn.pack(side='right')
        
        # Info button
        info_btn = self.create_modern_button(export_frame, "ℹ️ About", 
                                            self.show_about, 'primary')
        info_btn.pack(side='right', padx=(0, 10))
        self.create_tooltip(info_btn, "About Label Print Server")
        
        # Start periodic updates
        self.after(1000, self.update_status)
        self.after(2000, self.reload_table_periodic)
        
        # Add double click handler to table
        self.tree.bind('<Double-1>', self.on_row_double)

    def show_about(self):
        """Show modern scrollable about dialog"""
        about_window = tk.Toplevel(self)
        about_window.title("About Label Print Server")
        about_window.geometry("500x600")
        about_window.configure(bg='#f0f0f0')
        about_window.resizable(True, True)
        about_window.minsize(450, 500)
        
        # Center the window
        about_window.transient(self)
        about_window.grab_set()
        
        # Main container with scrollable area
        main_container = tk.Frame(about_window, bg='#f0f0f0')
        main_container.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Create canvas and scrollbar for scrollable content
        canvas = tk.Canvas(main_container, bg='#ffffff', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#ffffff')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Content inside scrollable frame
        content_frame = tk.Frame(scrollable_frame, bg='#ffffff')
        content_frame.pack(fill='both', expand=True, padx=25, pady=25)
        
        # Header with icon
        header_frame = tk.Frame(content_frame, bg='#ffffff')
        header_frame.pack(fill='x', pady=(0, 20))
        
        title_label = tk.Label(header_frame, text="📄 Label Print Server", 
                              font=('Arial', 18, 'bold'), bg='#ffffff', fg='#2c3e50')
        title_label.pack()
        
        version_label = tk.Label(header_frame, text="Version 2.0 - Modern Edition", 
                                font=('Arial', 11), bg='#ffffff', fg='#7f8c8d')
        version_label.pack(pady=(5, 0))
        
        # Separator
        separator1 = tk.Frame(content_frame, height=2, bg='#ecf0f1')
        separator1.pack(fill='x', pady=(10, 20))
        
        # Description
        desc_frame = tk.Frame(content_frame, bg='#ffffff')
        desc_frame.pack(fill='x', pady=(0, 25))
        
        desc_title = tk.Label(desc_frame, text="📋 Overview", 
                             font=('Arial', 12, 'bold'), bg='#ffffff', fg='#2c3e50')
        desc_title.pack(anchor='w', pady=(0, 10))
        
        description = """A comprehensive Windows application designed for warehouse and retail environments. 
This modern tool allows users to quickly look up customer information from SQL Server databases 
by scanning or entering quotation numbers, then print professional customer labels directly 
to Windows printers. The application features a clean, intuitive interface with real-time 
server monitoring and advanced data management capabilities."""
        
        desc_label = tk.Label(desc_frame, text=description, 
                             font=('Arial', 10), bg='#ffffff', fg='#34495e',
                             wraplength=430, justify='left')
        desc_label.pack(anchor='w')
        
        # Features
        features_frame = tk.Frame(content_frame, bg='#ffffff')
        features_frame.pack(fill='x', pady=(0, 25))
        
        features_title = tk.Label(features_frame, text="✨ Key Features", 
                                 font=('Arial', 12, 'bold'), bg='#ffffff', fg='#2c3e50')
        features_title.pack(anchor='w', pady=(0, 10))
        
        features_list = """🔄 Real-time server status monitoring with automatic reconnection
🔍 Dynamic search with instant results and pagination
📊 CSV export and clipboard functionality for data sharing
🖥️ System tray integration for seamless background operation
🎨 Modern UI with intuitive icons, tooltips, and responsive design
📱 Cross-browser compatibility for Raspberry Pi terminals
🏢 SQL Server integration with Windows Authentication
🖨️ Direct Windows printer integration via system commands
⏰ Automatic timestamp conversion to local timezone
🔧 Runtime configuration with connection validation"""
        
        features_text = tk.Label(features_frame, text=features_list, 
                                font=('Arial', 10), bg='#ffffff', fg='#34495e',
                                justify='left')
        features_text.pack(anchor='w')
        
        # Technical Details
        tech_frame = tk.Frame(content_frame, bg='#ffffff')
        tech_frame.pack(fill='x', pady=(0, 25))
        
        tech_title = tk.Label(tech_frame, text="🔧 Technical Details", 
                             font=('Arial', 12, 'bold'), bg='#ffffff', fg='#2c3e50')
        tech_title.pack(anchor='w', pady=(0, 10))
        
        tech_details = """Framework: Flask web server with Waitress WSGI
Database: SQL Server with Windows Authentication
Frontend: Modern HTML5 with real-time JavaScript
GUI: Python Tkinter with TTK modern styling
Threading: Multi-process architecture for stability
Platform: Windows Server with printer access
Network: Designed for local network deployment"""
        
        tech_text = tk.Label(tech_frame, text=tech_details, 
                            font=('Arial', 10), bg='#ffffff', fg='#34495e',
                            justify='left')
        tech_text.pack(anchor='w')
        
        # Usage Instructions
        usage_frame = tk.Frame(content_frame, bg='#ffffff')
        usage_frame.pack(fill='x', pady=(0, 25))
        
        usage_title = tk.Label(usage_frame, text="📖 Quick Start Guide", 
                              font=('Arial', 12, 'bold'), bg='#ffffff', fg='#2c3e50')
        usage_title.pack(anchor='w', pady=(0, 10))
        
        usage_text = """1. Configure database connection via Settings (⚙️) button
2. Start the server using the Start Server button
3. Access web interface at http://localhost:5000
4. Enter quotation numbers to lookup customer information  
5. Print labels directly from the web interface
6. Monitor activity via this management GUI
7. Use search and export features for data analysis"""
        
        usage_label = tk.Label(usage_frame, text=usage_text, 
                              font=('Arial', 10), bg='#ffffff', fg='#34495e',
                              justify='left')
        usage_label.pack(anchor='w')
        
        # Separator
        separator2 = tk.Frame(content_frame, height=2, bg='#ecf0f1')
        separator2.pack(fill='x', pady=(15, 20))
        
        # Close button
        button_frame = tk.Frame(content_frame, bg='#ffffff')
        button_frame.pack(fill='x')
        
        close_btn = self.create_modern_button(button_frame, "✅ Close", 
                                             about_window.destroy, 'primary')
        close_btn.pack(pady=10)
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Cleanup mousewheel binding when window closes
        def cleanup_bindings():
            canvas.unbind_all("<MouseWheel>")
            about_window.destroy()
        
        about_window.protocol("WM_DELETE_WINDOW", cleanup_bindings)
        close_btn.configure(command=cleanup_bindings)

    def update_status(self):
        """Update server status with non-blocking timeout and error resilience"""
        running = False
        status_text = "Checking..."
        
        try:
            # Use very short timeout to prevent GUI blocking
            r = requests.get('http://localhost:5000/get-settings', timeout=0.3)
            if r.status_code == 200:
                running = True
                status_text = "Running"
            else:
                status_text = f"Error ({r.status_code})"
        except requests.exceptions.Timeout:
            status_text = "Server Timeout"
        except requests.exceptions.ConnectionError:
            status_text = "Stopped"
        except Exception as e:
            status_text = f"Error: {str(e)[:20]}..."
            
        # Update GUI elements with error protection
        try:
            self.status_label.config(text=f"Server Status: {status_text}")
            
            # Update status indicator color
            if running:
                self.status_indicator.config(fg='#28a745')  # Green for running
            elif "Error" in status_text:
                self.status_indicator.config(fg='#dc3545')  # Red for error
            else:
                self.status_indicator.config(fg='#ffc107')  # Yellow for stopped/checking
        except Exception:
            pass
        
        # Enable/disable start/stop buttons with error protection
        try:
            if running:
                self.start_btn.config(state='disabled')
                self.stop_btn.config(state='normal')
            else:
                self.start_btn.config(state='normal')
                self.stop_btn.config(state='disabled')
        except Exception:
            pass

        # Update startup status periodically (every 30 seconds)
        if not hasattr(self, '_startup_check_counter'):
            self._startup_check_counter = 0
        
        self._startup_check_counter += 1
        if self._startup_check_counter >= 10:  # Check every 30 seconds (10 * 3 seconds)
            self._startup_check_counter = 0
            try:
                self.check_startup_status()
            except Exception:
                pass  # Ignore errors in startup status check

        # Schedule next update - use longer interval to reduce load
        self.after(3000, self.update_status)

    def save_window_info(self):
        """Save window handle and process info for tray restoration"""
        try:
            # Wait a bit for window to be fully created
            self.after(100, self._save_window_info_delayed)
        except Exception as e:
            print(f'Error saving window info: {e}')

    def _save_window_info_delayed(self):
        """Delayed window info saving after window is fully created"""
        try:
            hwnd = self.winfo_id()  # Get tkinter window handle
            pid = os.getpid()
            
            window_info = {
                'hwnd': hwnd,
                'pid': pid,
                'title': self.title()
            }
            
            # Save to temp file that tray app can read
            temp_dir = tempfile.gettempdir()
            info_file = os.path.join(temp_dir, 'label_print_gui_info.json')
            
            with open(info_file, 'w') as f:
                json.dump(window_info, f)
                
            print(f'Saved window info: hwnd={hwnd}, pid={pid}')
            
        except Exception as e:
            print(f'Error in delayed window info save: {e}')

    def check_restore_signal(self):
        """Check if tray app is requesting window restoration"""
        try:
            temp_dir = tempfile.gettempdir()
            restore_file = os.path.join(temp_dir, 'label_print_restore_signal.tmp')
            
            if os.path.exists(restore_file):
                # Restore signal found, show the window
                try:
                    os.remove(restore_file)  # Remove signal file
                except Exception:
                    pass
                
                # Restore window using the dedicated method
                self.restore_from_tray()
                print('GUI restored via signal file')
                
        except Exception as e:
            print(f'Error checking restore signal: {e}')
        
        # Check again in 500ms
        self.after(500, self.check_restore_signal)

    def start_server(self):
        try:
            # First, check if server is running by trying HTTP
            if self.is_server_running():
                # Server is already running, no need to start
                messagebox.showinfo('Info', 'Server is already running')
                self.force_status_update()
                return
            
            # Check if tray application is running
            if not self.is_tray_app_running():
                messagebox.showerror("Error", "Tray application is not running. Please start the tray application first.")
                return
            
            # Server is not running, use file-based signaling
            print("Server not running, using file-based start signal...")
            
            try:
                # Create start signal file for the tray app to detect
                start_signal_file = os.path.join(os.path.dirname(__file__), '.tray_start_signal')
                with open(start_signal_file, 'w') as f:
                    f.write('start')
                
                messagebox.showinfo('Info', 'Server start requested via signal file')
                print("Created start signal file")
                
                # Force multiple status updates to ensure GUI responds when server comes up
                self.after(1000, self.force_status_update)   # First check after 1s
                self.after(2500, self.force_status_update)   # Second check after 2.5s
                self.after(4000, self.force_status_update)   # Final check after 4s
                
            except Exception as e:
                print(f"Error creating start signal file: {e}")
                messagebox.showerror("Error", f"Failed to create start signal: {e}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {e}")
            
            # Update status to check current state
            self.after(500, self.force_status_update)

    def is_server_running(self):
        try:
            r = requests.get('http://127.0.0.1:5000/get-settings', timeout=1)
            return r.status_code == 200
        except Exception:
            return False

    def is_tray_app_running(self):
        """Check if tray application is running using multiple methods"""
        try:
            # Method 1: Check for control token file
            token_file = os.path.join(os.path.dirname(__file__), '.tray_control_token')
            if os.path.exists(token_file):
                return True
            
            # Method 2: Try to detect tray process by checking for tray-specific files
            # The tray app should create this file when it starts and remove it when it exits
            tray_pid_file = os.path.join(os.path.dirname(__file__), '.tray_running')
            if os.path.exists(tray_pid_file):
                return True
            
            # Method 3: Check if we can create a start signal file (directory writable)
            # If the directory is not writable, the tray app might not be running properly
            try:
                test_file = os.path.join(os.path.dirname(__file__), '.tray_test')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                # If we can write files, assume tray app can read them
                return True
            except Exception:
                return False
                
        except Exception:
            return False

    def minimize_to_tray(self):
        try:
            # simply withdraw the window; tray app is separate and remains running
            self.withdraw()
            print('GUI withdrawn to tray')
        except Exception as e:
            print('minimize_to_tray error', e)

    def quit_requested(self):
        # Check if server is running
        running = self.is_server_running()
        
        if running:
            # Server is running - ask user what to do
            result = messagebox.askyesnocancel(
                'Confirm Quit', 
                'Server is currently running.\n\n'
                'Do you want to stop the server and quit the entire program?\n\n'
                'Yes = Stop server and quit everything\n'
                'No = Quit GUI only (server keeps running)\n'
                'Cancel = Don\'t quit'
            )
            
            if result is None:  # Cancel
                return
            elif result:  # Yes - stop server and quit everything
                print('User chose to stop server and quit completely')
                self.quit_everything()
                return
            else:  # No - quit GUI only
                print('User chose to quit GUI only, server will keep running')
                self.destroy()
                return
        else:
            # Server is not running - ask if they want to quit everything
            result = messagebox.askyesno(
                'Confirm Quit', 
                'Do you want to quit the entire program including the tray application?\n\n'
                'Yes = Quit everything (including tray)\n'
                'No = Quit GUI only (tray keeps running)'
            )
            
            if result:  # Yes - quit everything
                print('User chose to quit everything')
                self.quit_everything()
                return
            else:  # No - quit GUI only
                print('User chose to quit GUI only')
                self.destroy()
                return

    def quit_everything(self):
        """Quit the entire program including server and tray application"""
        import os  # Import at method level to avoid scoping issues
        
        try:
            print('Attempting to quit everything (server + tray)...')
            
            # Check if server is running to determine method
            if self.is_server_running():
                # Server is running, use HTTP to send quit command
                print('Server is running, using HTTP quit command...')
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

                    # Send quit command to tray app (this will stop server and exit tray)
                    payload = {'action': 'quit', 'token': token}
                    r = requests.post('http://127.0.0.1:5000/control', json=payload, timeout=3)
                    
                    if r.status_code == 200:
                        print('HTTP quit command sent successfully')
                    else:
                        print(f'HTTP quit command error: {r.status_code} {r.text}')
                        # Fall back to file-based method
                        self._quit_via_signal()
                        
                except Exception as e:
                    print(f'Error with HTTP quit: {e}')
                    # Fall back to file-based method
                    self._quit_via_signal()
            else:
                # Server is not running, use file-based signaling
                print('Server is not running, using file-based quit signal...')
                self._quit_via_signal()
                
        except Exception as e:
            print(f'Error in quit_everything: {e}')
        
        # Close GUI regardless of whether tray quit worked
        self.destroy()
        
        # Exit this GUI process
        os._exit(0)
    
    def _quit_via_signal(self):
        """Send quit signal via file (for when server is not running)"""
        import os  # Import at method level to avoid scoping issues
        
        try:
            quit_signal_file = os.path.join(os.path.dirname(__file__), '.tray_quit_signal')
            with open(quit_signal_file, 'w') as f:
                f.write('quit')
            print('Created quit signal file for tray app')
        except Exception as e:
            print(f'Error creating quit signal file: {e}')

    def stop_server_and_quit(self):
        """Legacy method - redirect to quit_everything"""
        self.quit_everything()
            
        # Close GUI
        self.destroy()
        
        # Exit the GUI process completely
        os._exit(0)

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
                
                # Force multiple status updates to ensure GUI responds
                self.after(300, self.force_status_update)   # Quick first check
                self.after(1000, self.force_status_update)  # Second check
                self.after(2000, self.force_status_update)  # Final check
                
            else:
                messagebox.showerror('Error', f'Control endpoint error: {r.status_code} {r.text}')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop server: {e}")
            
            # Even if stop failed, update status to check current state
            self.after(500, self.force_status_update)

    def force_status_update(self):
        """Force an immediate status update and refresh GUI state with threading"""
        import threading
        
        def check_status_async():
            """Check server status in background thread to prevent GUI blocking"""
            running = False
            status_text = "Checking..."
            
            try:
                # Very short timeout to prevent blocking
                r = requests.get('http://localhost:5000/get-settings', timeout=0.2)
                if r.status_code == 200:
                    running = True
                    status_text = "Running"
                else:
                    status_text = f"Error ({r.status_code})"
            except requests.exceptions.Timeout:
                status_text = "Stopped (Timeout)"
            except requests.exceptions.ConnectionError:
                status_text = "Stopped"
            except Exception as e:
                status_text = f"Error: {str(e)[:15]}..."
            
            # Update GUI from main thread
            self.after(0, lambda: self.update_gui_status(running, status_text))
        
        # Run status check in background thread
        status_thread = threading.Thread(target=check_status_async, daemon=True)
        status_thread.start()
    
    def update_gui_status(self, running, status_text):
        """Update GUI elements from main thread - thread-safe"""
        try:
            self.status_label.config(text=f"Server Status: {status_text}")
            
            # Update status indicator color
            if running:
                self.status_indicator.config(fg='#28a745')  # Green for running
            elif "Error" in status_text:
                self.status_indicator.config(fg='#dc3545')  # Red for error
            else:
                self.status_indicator.config(fg='#ffc107')  # Yellow for stopped/checking
        except Exception:
            pass
        
        # Enable/disable start/stop buttons
        try:
            if running:
                self.start_btn.config(state='disabled')
                self.stop_btn.config(state='normal')
            else:
                self.start_btn.config(state='normal')
                self.stop_btn.config(state='disabled')
        except Exception as e:
            print(f'Error updating button states: {e}')
        
        print(f'GUI Status updated: Server is {"running" if running else "stopped"}')
        
        # Force GUI to refresh
        try:
            self.update_idletasks()
        except Exception:
            pass

    def open_browser(self):
        webbrowser.open('http://localhost:5000')

    def on_search(self):
        q = self.search_var.get().strip()
        self.current_page = 1
        self.reload_table(query=q, page=self.current_page)

    def reload_table(self, query=None, page=None):
        try:
            params = {}
            if query:
                params['q'] = query
            # requested page (use current_page if not provided)
            requested_page = page if page is not None else self.current_page
            params['page'] = requested_page
            params['page_size'] = self.page_size
            r = requests.get('http://127.0.0.1:5000/printed-records', params=params, timeout=3)
            if r.status_code == 200:
                data = r.json()
                if data.get('success') is False:
                    messagebox.showerror('Error', f"Printed records error: {data.get('error')}")
                    return
                records = data.get('records', [])
                total = data.get('total', 0)
                page_size = data.get('page_size', self.page_size)
                has_more = data.get('has_more', False)
                # Prefer the requested page as authoritative for display; fall back to server page
                server_page = data.get('page')
                self.current_page = requested_page if requested_page is not None else (server_page or 1)
                # update controls
                self.page_label.config(text=f'Page {self.current_page} (showing {len(records)} of {total})')
                self.prev_btn.config(state=('normal' if self.current_page > 1 else 'disabled'))
                self.next_btn.config(state=('normal' if has_more else 'disabled'))
                # Clear tree
                for i in self.tree.get_children():
                    self.tree.delete(i)
                for rec in records:
                    # format printed_at nicely if ISO and convert UTC to local time
                    printed_at = rec.get('printed_at')
                    try:
                        # try parsing ISO format
                        from datetime import datetime, timezone
                        dt = datetime.fromisoformat(printed_at)
                        
                        # If the datetime has no timezone info, assume it's UTC (old records)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        
                        # Convert to local time
                        local_dt = dt.astimezone()
                        printed_at_str = local_dt.strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        printed_at_str = printed_at
                    addr = rec.get('address') or ''
                    # truncate/wrap address for table cell
                    if len(addr) > 120:
                        addr_display = addr[:117] + '...'
                    else:
                        addr_display = addr
                    # Insert values in the new column order: id, printed_at, quotation, party, address, phone, mobile
                    self.tree.insert('', 'end', values=(rec.get('id'), printed_at_str, rec.get('quotation'), rec.get('party') or '', addr_display, rec.get('phone') or '', rec.get('mobile') or ''))
            else:
                print('reload_table failed', r.status_code, r.text)
        except Exception as e:
            # If the server is down or connection refused, avoid noisy tracebacks.
            # Treat this as server stopped: clear table and disable paging controls.
            import requests as _requests
            if isinstance(e, (_requests.exceptions.RequestException,)):
                # Clear tree
                try:
                    for i in self.tree.get_children():
                        self.tree.delete(i)
                except Exception:
                    pass
                try:
                    self.page_label.config(text='Server not running')
                    self.prev_btn.config(state='disabled')
                    self.next_btn.config(state='disabled')
                except Exception:
                    pass
                # Update status label as well
                try:
                    self.status_label.config(text='Server Status: Stopped')
                except Exception:
                    pass
                return
            # Fallback: log unexpected exceptions
            print('reload_table exception', e)

    def reload_table_periodic(self):
        """Reload table periodically with async loading to prevent GUI freezing"""
        import threading
        
        def load_table_async():
            try:
                q = self.search_var.get().strip()
                self.reload_table(query=q if q else None, page=self.current_page)
            except Exception as e:
                print(f'Error in periodic table reload: {e}')
        
        # Load table data in background thread
        load_thread = threading.Thread(target=load_table_async, daemon=True)
        load_thread.start()
        
        # Schedule next periodic update
        self.after(5000, self.reload_table_periodic)  # Increased interval to reduce load

    def on_prev(self):
        if self.current_page > 1:
            self.current_page -= 1
            q = self.search_var.get().strip()
            self.reload_table(query=q if q else None, page=self.current_page)

    def on_next(self):
        self.current_page += 1
        q = self.search_var.get().strip()
        self.reload_table(query=q if q else None, page=self.current_page)

    def export_csv(self):
        try:
            import csv
            rows = []
            cols = ('id','printed_at','quotation','party','address','phone','mobile')
            for iid in self.tree.get_children():
                values = self.tree.item(iid)['values']
                rows.append(values)
            if not rows:
                messagebox.showinfo('Export', 'No rows to export')
                return
            # ask for file path under program dir
            from tkinter.filedialog import asksaveasfilename
            path = asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files','*.csv')], initialfile='printed_records.csv')
            if not path:
                return
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(cols)
                for r in rows:
                    writer.writerow(r)
            messagebox.showinfo('Export', f'Exported {len(rows)} rows to {path}')
        except Exception as e:
            messagebox.showerror('Export failed', str(e))

    def copy_selected(self):
        try:
            sel = self.tree.selection()
            if not sel:
                messagebox.showinfo('Copy', 'No selection')
                return
            lines = []
            for iid in sel:
                vals = self.tree.item(iid)['values']
                lines.append('\t'.join([str(v) for v in vals]))
            s = '\n'.join(lines)
            self.clipboard_clear()
            self.clipboard_append(s)
            messagebox.showinfo('Copy', 'Selected rows copied to clipboard (tab-separated)')
        except Exception as e:
            messagebox.showerror('Copy failed', str(e))

    def on_row_double(self, event):
        try:
            iid = self.tree.identify_row(event.y)
            if not iid:
                return
            vals = self.tree.item(iid)['values']
            # Show a details dialog
            cols = ('ID','Printed At','Quotation','Party','Address','Phone','Mobile')
            details = '\n'.join([f'{c}: {v}' for c,v in zip(cols, vals)])
            # Show in info box
            messagebox.showinfo('Record details', details)
        except Exception as e:
            print('on_row_double error', e)

    def on_map(self, event):
        """Handle window map (show) event"""
        self.is_mapped = True
    
    def on_unmap(self, event):
        """Handle window unmap event - could be minimize or hide"""
        if event.widget == self:  # Only handle events for main window
            self.is_mapped = False
            # Check if this was due to iconify (minimize button)
            # Use after_idle to check state after the event is processed
            self.after_idle(self.check_if_minimized)
    
    def check_if_minimized(self):
        """Check if window was minimized and hide to tray if so"""
        try:
            current_state = self.state()
            if current_state == 'iconic':
                # Window was minimized, hide it to tray instead
                self.withdraw()
                print("GUI minimized to tray via minimize button")
        except Exception as e:
            print(f"Error checking minimize state: {e}")
    
    def restore_from_tray(self):
        """Restore window from tray"""
        self.deiconify()
        self.lift()
        self.focus_force()
        print("GUI restored from tray")
    
    def on_close(self):
        """Handle window close event - minimize to tray instead of closing"""
        self.minimize_to_tray()


def check_single_instance_gui():
    """Check if another GUI instance is already running"""
    gui_running_file = os.path.join(os.path.dirname(__file__), '.gui_running')
    
    if os.path.exists(gui_running_file):
        try:
            with open(gui_running_file, 'r') as f:
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
                        # Process exists - kill it and start fresh
                        print(f"Found existing GUI process {existing_pid}, killing it...")
                        try:
                            import subprocess
                            subprocess.run(['taskkill', '/F', '/PID', str(existing_pid)], 
                                         capture_output=True, timeout=5)
                            import time
                            time.sleep(0.5)
                            # Remove the file after killing
                            if os.path.exists(gui_running_file):
                                os.remove(gui_running_file)
                        except Exception as e:
                            print(f"Error killing existing GUI: {e}")
                        return True  # Continue with starting new instance
                else:
                    # For non-Windows (though this is a Windows app)
                    os.kill(existing_pid, 0)
                    return False  # Process exists
            except (OSError, ValueError):
                # Process doesn't exist, remove stale file
                print(f"Removing stale GUI running file (PID {existing_pid} not found)")
                try:
                    os.remove(gui_running_file)
                except OSError:
                    pass
        except Exception as e:
            # Error reading file, assume it's stale
            print(f"Error reading GUI running file: {e}")
            try:
                os.remove(gui_running_file)
            except OSError:
                pass
    
    return True  # No other instance running or cleaned up successfully

if __name__ == '__main__':
    # Check for single instance and clean up if needed
    check_single_instance_gui()  # Always returns True now or cleans up
    
    # Create GUI instance indicator file
    gui_running_file = os.path.join(os.path.dirname(__file__), '.gui_running')
    try:
        with open(gui_running_file, 'w') as f:
            f.write(str(os.getpid()))
    except Exception as e:
        print(f"Warning: Could not create GUI running file: {e}")
    
    # Register cleanup function
    def cleanup_gui_file():
        try:
            if os.path.exists(gui_running_file):
                os.remove(gui_running_file)
        except Exception:
            pass
    
    import atexit
    atexit.register(cleanup_gui_file)
    
    app = TrayGUI()
    try:
        app.mainloop()
    finally:
        cleanup_gui_file()
