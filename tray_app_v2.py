"""
Label Print Server - Modern System Tray Application
Single-process implementation with integrated GUI
"""

import os
import sys
import threading
import webbrowser
import winreg
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk, font as tkfont
import PIL.Image
import pystray
from pystray import MenuItem as item
from datetime import datetime

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app import app
from waitress import serve
from update_manager import UpdateManager
from printed_db import init_db, get_recent

# =============================================================================
# CONFIGURATION
# =============================================================================

APP_DIR = Path(__file__).parent

# Use AppData for lock file when installed in Program Files
if 'Program Files' in str(APP_DIR):
    data_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))) / 'LabelPrintServer' / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    LOCK_FILE = data_dir / '.tray_running'
else:
    LOCK_FILE = APP_DIR / '.tray_running'

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5000

# =============================================================================
# SERVER MANAGER
# =============================================================================

class ServerManager:
    """Manages the Flask/Waitress server lifecycle"""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.running = False
        self.thread = None
        self.server = None
    
    def is_running(self):
        with self.lock:
            return self.running
    
    def start(self):
        """Start the server in a background thread"""
        with self.lock:
            if self.running:
                print("Server already running")
                return False
            
            print("Starting server...")
            self.thread = threading.Thread(target=self._run_server, daemon=True)
            self.thread.start()
            return True
    
    def stop(self):
        """Stop the running server"""
        with self.lock:
            if not self.running:
                print("Server not running")
                return False
            
            print("Stopping server...")
            if self.server:
                self.server.close()
            
            self.running = False
            return True
    
    def _run_server(self):
        """Run server (internal use only)"""
        with self.lock:
            self.running = True
            
        try:
            print("Creating Waitress server...")
            from waitress import create_server
            
            server = create_server(
                app,
                host=SERVER_HOST,
                port=SERVER_PORT,
                threads=4,
                channel_timeout=30
            )
            
            with self.lock:
                self.server = server
            
            print(f"Server listening on http://{SERVER_HOST}:{SERVER_PORT}")
            server.run()
            
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            with self.lock:
                self.running = False
                self.server = None
            print("Server stopped")

# =============================================================================
# GUI MANAGER
# =============================================================================

class GUIManager:
    """Manages the settings GUI window"""
    
    def __init__(self, server_mgr, quit_callback):
        self.server_mgr = server_mgr
        self.quit_callback = quit_callback
        self.window = None
        self.root = None
        self.lock = threading.Lock()
        self.update_manager = UpdateManager()
        self.available_update = None
        
        # Database pagination
        self.db_page = 0
        self.db_page_size = 50
        self.db_search_query = ""
    
    def show(self):
        """Show the GUI window (creates if needed, restores if minimized)"""
        with self.lock:
            if self.window and self.window.winfo_exists():
                # Window exists, just restore and focus
                self.window.deiconify()
                self.window.lift()
                self.window.focus_force()
            else:
                # Create new window in main thread
                self._create_window()
    
    def _create_window(self):
        """Create the GUI window"""
        self.window = tk.Toplevel(self.root) if self.root else tk.Tk()
        self.window.title("📄 Label Print Server")
        self.window.geometry("900x600")
        self.window.resizable(True, True)
        
        # Set icon if available
        icon_path = APP_DIR / 'icons' / 'app_icon.ico'
        if icon_path.exists():
            try:
                self.window.iconbitmap(str(icon_path))
            except:
                pass
        
        # Configure window close behavior
        self.window.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill='both', expand=True)
        
        # Create tabs
        self.control_tab = tk.Frame(self.notebook, bg='white')
        self.database_tab = tk.Frame(self.notebook, bg='white')
        self.update_tab = tk.Frame(self.notebook, bg='white')
        
        self.notebook.add(self.control_tab, text='  Server Control  ')
        self.notebook.add(self.database_tab, text='  Print History  ')
        self.notebook.add(self.update_tab, text='  Updates  ')
        
        # Create UI for each tab
        self._create_control_ui()
        self._create_database_ui()
        self._create_update_ui()
        
        # Update status
        self._update_status()
        
        # Start status update timer
        self._schedule_status_update()
        
        # Load database records
        self._load_database_records()
        
        # Check for updates in background
        threading.Thread(target=self._check_for_updates_background, daemon=True).start()
    
    def _create_control_ui(self):
        """Create the server control UI"""
        parent = self.control_tab
        
        # Header
        header = tk.Frame(parent, bg='#2c3e50', height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        title = tk.Label(header, text="📄 Label Print Server", 
                        font=('Arial', 18, 'bold'), 
                        bg='#2c3e50', fg='white')
        title.pack(pady=25)
        
        # Status section
        status_frame = tk.Frame(parent, bg='white', pady=20)
        status_frame.pack(fill='x', padx=20, pady=20)
        
        tk.Label(status_frame, text="Server Status:", 
                font=('Arial', 12, 'bold'), bg='white').pack()
        
        self.status_label = tk.Label(status_frame, text="Checking...", 
                                     font=('Arial', 11), bg='white', fg='#7f8c8d')
        self.status_label.pack(pady=5)
        
        # Control buttons
        btn_frame = tk.Frame(parent, bg='white')
        btn_frame.pack(pady=10)
        
        self.start_btn = tk.Button(btn_frame, text="▶️ Start Server", 
                                   command=self._start_server,
                                   font=('Arial', 10), 
                                   bg='#27ae60', fg='white',
                                   padx=20, pady=10, width=15,
                                   relief='flat', cursor='hand2')
        self.start_btn.pack(side='left', padx=5)
        
        self.stop_btn = tk.Button(btn_frame, text="⏹️ Stop Server", 
                                  command=self._stop_server,
                                  font=('Arial', 10), 
                                  bg='#e74c3c', fg='white',
                                  padx=20, pady=10, width=15,
                                  relief='flat', cursor='hand2')
        self.stop_btn.pack(side='left', padx=5)
        
        # Additional buttons
        misc_frame = tk.Frame(parent, bg='white')
        misc_frame.pack(pady=10)
        
        tk.Button(misc_frame, text="🌐 Open Browser", 
                 command=self._open_browser,
                 font=('Arial', 10), 
                 bg='#3498db', fg='white',
                 padx=20, pady=10, width=15,
                 relief='flat', cursor='hand2').pack(side='left', padx=5)
        
        tk.Button(misc_frame, text="⚙️ Settings", 
                 command=self._open_settings,
                 font=('Arial', 10), 
                 bg='#95a5a6', fg='white',
                 padx=20, pady=10, width=15,
                 relief='flat', cursor='hand2').pack(side='left', padx=5)
    
    def _update_status(self):
        """Update server status display"""
        if self.window and self.window.winfo_exists():
            if self.server_mgr.is_running():
                self.status_label.config(text="✅ Running", fg='#27ae60')
                self.start_btn.config(state='disabled')
                self.stop_btn.config(state='normal')
            else:
                self.status_label.config(text="⏹️ Stopped", fg='#e74c3c')
                self.start_btn.config(state='normal')
                self.stop_btn.config(state='disabled')
    
    def _schedule_status_update(self):
        """Schedule periodic status updates"""
        if self.window and self.window.winfo_exists():
            self._update_status()
            self.window.after(1000, self._schedule_status_update)
    
    def _start_server(self):
        if self.server_mgr.start():
            messagebox.showinfo("Success", "Server started successfully!")
        self._update_status()
    
    def _stop_server(self):
        if self.server_mgr.stop():
            messagebox.showinfo("Success", "Server stopped successfully!")
        self._update_status()
    
    def _open_browser(self):
        webbrowser.open(f"http://localhost:{SERVER_PORT}")
    
    def _open_settings(self):
        webbrowser.open(f"http://localhost:{SERVER_PORT}")
    
    def _create_database_ui(self):
        """Create the print history database UI"""
        parent = self.database_tab
        
        # Header
        header_frame = tk.Frame(parent, bg='#34495e', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="📋 Print History Database", 
                font=('Arial', 14, 'bold'), bg='#34495e', fg='white').pack(pady=15)
        
        # Search frame
        search_frame = tk.Frame(parent, bg='white', pady=10)
        search_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(search_frame, text="🔍 Search:", font=('Arial', 10), 
                bg='white').pack(side='left', padx=5)
        
        self.db_search_entry = tk.Entry(search_frame, font=('Arial', 10), width=30)
        self.db_search_entry.pack(side='left', padx=5)
        self.db_search_entry.bind('<Return>', lambda e: self._search_database())
        
        tk.Button(search_frame, text="Search", command=self._search_database,
                 font=('Arial', 9), bg='#3498db', fg='white',
                 padx=15, pady=5, relief='flat', cursor='hand2').pack(side='left', padx=5)
        
        tk.Button(search_frame, text="Clear", command=self._clear_search,
                 font=('Arial', 9), bg='#95a5a6', fg='white',
                 padx=15, pady=5, relief='flat', cursor='hand2').pack(side='left', padx=5)
        
        # Results info
        self.db_results_label = tk.Label(parent, text="Loading...", 
                                         font=('Arial', 9), bg='white', fg='#7f8c8d')
        self.db_results_label.pack(pady=5)
        
        # Table frame with scrollbar
        table_frame = tk.Frame(parent, bg='white')
        table_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(table_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Treeview
        columns = ('ID', 'Quotation', 'Party', 'Phone', 'Mobile', 'Printed At')
        self.db_tree = ttk.Treeview(table_frame, columns=columns, show='headings',
                                    yscrollcommand=scrollbar.set, height=15)
        
        # Configure columns
        self.db_tree.heading('ID', text='ID')
        self.db_tree.heading('Quotation', text='Quotation')
        self.db_tree.heading('Party', text='Party Name')
        self.db_tree.heading('Phone', text='Phone')
        self.db_tree.heading('Mobile', text='Mobile')
        self.db_tree.heading('Printed At', text='Printed At')
        
        self.db_tree.column('ID', width=50, anchor='center')
        self.db_tree.column('Quotation', width=100)
        self.db_tree.column('Party', width=200)
        self.db_tree.column('Phone', width=100)
        self.db_tree.column('Mobile', width=100)
        self.db_tree.column('Printed At', width=150)
        
        self.db_tree.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.db_tree.yview)
        
        # Pagination
        pag_frame = tk.Frame(parent, bg='white', pady=10)
        pag_frame.pack(fill='x', padx=20)
        
        self.prev_btn = tk.Button(pag_frame, text="◀ Previous", command=self._prev_page,
                                  font=('Arial', 9), bg='#95a5a6', fg='white',
                                  padx=15, pady=5, relief='flat', cursor='hand2')
        self.prev_btn.pack(side='left', padx=5)
        
        self.page_label = tk.Label(pag_frame, text="Page 1", font=('Arial', 10), bg='white')
        self.page_label.pack(side='left', padx=20)
        
        self.next_btn = tk.Button(pag_frame, text="Next ▶", command=self._next_page,
                                  font=('Arial', 9), bg='#95a5a6', fg='white',
                                  padx=15, pady=5, relief='flat', cursor='hand2')
        self.next_btn.pack(side='left', padx=5)
        
        tk.Button(pag_frame, text="🔄 Refresh", command=self._load_database_records,
                 font=('Arial', 9), bg='#3498db', fg='white',
                 padx=15, pady=5, relief='flat', cursor='hand2').pack(side='right', padx=5)
    
    def _create_update_ui(self):
        """Create the updates UI"""
        parent = self.update_tab
        
        # Header
        header_frame = tk.Frame(parent, bg='#9b59b6', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="🔄 Update Manager", 
                font=('Arial', 14, 'bold'), bg='#9b59b6', fg='white').pack(pady=15)
        
        # Version info
        version_frame = tk.Frame(parent, bg='white', pady=20)
        version_frame.pack(fill='x', padx=20, pady=20)
        
        tk.Label(version_frame, text="Current Version:", font=('Arial', 11, 'bold'),
                bg='white').pack(anchor='w')
        self.current_version_label = tk.Label(version_frame, 
                                              text=f"v{self.update_manager.current_version}",
                                              font=('Arial', 14), bg='white', fg='#27ae60')
        self.current_version_label.pack(anchor='w', pady=5)
        
        # Update status
        self.update_status_label = tk.Label(version_frame, text="Checking for updates...",
                                           font=('Arial', 10), bg='white', fg='#7f8c8d')
        self.update_status_label.pack(anchor='w', pady=10)
        
        # Changelog
        tk.Label(parent, text="Release Notes:", font=('Arial', 10, 'bold'),
                bg='white').pack(anchor='w', padx=20)
        
        changelog_frame = tk.Frame(parent, bg='white')
        changelog_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        changelog_scroll = tk.Scrollbar(changelog_frame)
        changelog_scroll.pack(side='right', fill='y')
        
        self.changelog_text = tk.Text(changelog_frame, wrap='word', height=10,
                                     yscrollcommand=changelog_scroll.set,
                                     font=('Arial', 9), bg='#f8f9fa',
                                     relief='solid', bd=1)
        self.changelog_text.pack(side='left', fill='both', expand=True)
        changelog_scroll.config(command=self.changelog_text.yview)
        
        # Buttons
        btn_frame = tk.Frame(parent, bg='white', pady=15)
        btn_frame.pack(fill='x', padx=20)
        
        tk.Button(btn_frame, text="🔍 Check for Updates", command=self._check_for_updates,
                 font=('Arial', 10), bg='#3498db', fg='white',
                 padx=20, pady=10, relief='flat', cursor='hand2').pack(side='left', padx=5)
        
        self.install_update_btn = tk.Button(btn_frame, text="📥 Install Update",
                                           command=self._install_update,
                                           font=('Arial', 10), bg='#27ae60', fg='white',
                                           padx=20, pady=10, relief='flat', cursor='hand2',
                                           state='disabled')
        self.install_update_btn.pack(side='left', padx=5)
    
    def _load_database_records(self):
        """Load database records"""
        try:
            # Initialize DB if needed
            init_db()
            
            # Get records
            offset = self.db_page * self.db_page_size
            result = get_recent(limit=self.db_page_size, q=self.db_search_query or None, offset=offset)
            
            # Clear existing items
            for item in self.db_tree.get_children():
                self.db_tree.delete(item)
            
            # Insert new items
            for record in result['records']:
                # Format datetime
                printed_at = record['printed_at']
                try:
                    dt = datetime.fromisoformat(printed_at)
                    printed_at = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
                
                self.db_tree.insert('', 'end', values=(
                    record['id'],
                    record['quotation'],
                    record['party'] or '',
                    record['phone'] or '',
                    record['mobile'] or '',
                    printed_at
                ))
            
            # Update pagination
            total = result['total']
            total_pages = (total // self.db_page_size) + (1 if total % self.db_page_size else 0)
            
            self.page_label.config(text=f"Page {self.db_page + 1} of {total_pages}")
            self.db_results_label.config(text=f"Showing {len(result['records'])} of {total} records")
            
            # Enable/disable pagination buttons
            self.prev_btn.config(state='normal' if self.db_page > 0 else 'disabled')
            self.next_btn.config(state='normal' if (self.db_page + 1) < total_pages else 'disabled')
            
        except Exception as e:
            self.db_results_label.config(text=f"Error loading records: {e}")
    
    def _search_database(self):
        """Search database"""
        self.db_search_query = self.db_search_entry.get().strip()
        self.db_page = 0
        self._load_database_records()
    
    def _clear_search(self):
        """Clear search"""
        self.db_search_entry.delete(0, 'end')
        self.db_search_query = ""
        self.db_page = 0
        self._load_database_records()
    
    def _next_page(self):
        """Next page"""
        self.db_page += 1
        self._load_database_records()
    
    def _prev_page(self):
        """Previous page"""
        if self.db_page > 0:
            self.db_page -= 1
            self._load_database_records()
    
    def _check_for_updates_background(self):
        """Check for updates in background"""
        try:
            result = self.update_manager.check_and_update(force=False)
            
            if self.window and self.window.winfo_exists():
                self.window.after(0, lambda: self._update_ui_after_check(result))
        except Exception as e:
            print(f"Background update check error: {e}")
    
    def _check_for_updates(self):
        """Manually check for updates"""
        self.update_status_label.config(text="🔍 Checking for updates...")
        
        def check():
            result = self.update_manager.check_and_update(force=True)
            if self.window and self.window.winfo_exists():
                self.window.after(0, lambda: self._update_ui_after_check(result))
        
        threading.Thread(target=check, daemon=True).start()
    
    def _update_ui_after_check(self, result):
        """Update UI after update check"""
        if result['status'] == 'update_available':
            self.available_update = result
            self.update_status_label.config(
                text=f"✨ Update Available: v{result['version']}", 
                fg='#27ae60'
            )
            self.install_update_btn.config(state='normal')
            
            # Show changelog
            self.changelog_text.delete('1.0', 'end')
            self.changelog_text.insert('1.0', result.get('changelog', 'No release notes available.'))
            
        elif result['status'] == 'no_update':
            self.update_status_label.config(text="✅ Up to date", fg='#27ae60')
            self.install_update_btn.config(state='disabled')
            self.changelog_text.delete('1.0', 'end')
            self.changelog_text.insert('1.0', 'You are running the latest version.')
            
        elif result['status'] == 'error':
            self.update_status_label.config(
                text=f"❌ Error: {result['message']}", 
                fg='#e74c3c'
            )
            self.install_update_btn.config(state='disabled')
    
    def _install_update(self):
        """Install available update"""
        if not self.available_update:
            return
        
        result = messagebox.askyesno(
            "Install Update",
            f"Install update v{self.available_update['version']}?\n\n"
            "The application will restart after installation."
        )
        
        if result:
            self.update_status_label.config(text="📥 Downloading update...")
            
            def install():
                try:
                    download_path = self.update_manager.download_update(self.available_update)
                    self.update_manager.install_update(download_path, self.available_update)
                    
                    if self.window and self.window.winfo_exists():
                        self.window.after(0, lambda: messagebox.showinfo(
                            "Update Complete",
                            "Update installed! Please restart the application."
                        ))
                except Exception as e:
                    if self.window and self.window.winfo_exists():
                        self.window.after(0, lambda: messagebox.showerror(
                            "Update Failed",
                            f"Failed to install update:\n{e}"
                        ))
            
            threading.Thread(target=install, daemon=True).start()
    
    def _minimize_to_tray(self):
        """Minimize window to tray"""
        if self.window:
            self.window.withdraw()
    
    def _on_window_close(self):
        """Handle window close button (X)"""
        result = messagebox.askyesnocancel(
            "Quit or Minimize?",
            "Do you want to quit the entire application?\n\n"
            "Yes = Quit everything\n"
            "No = Minimize to tray\n"
            "Cancel = Keep window open"
        )
        
        if result is None:  # Cancel
            return
        elif result:  # Yes - quit
            self._quit_app()
        else:  # No - minimize
            self._minimize_to_tray()
    
    def _quit_app(self):
        """Quit the entire application"""
        if self.server_mgr.is_running():
            result = messagebox.askyesno(
                "Confirm Quit",
                "Server is still running. Stop server and quit?"
            )
            if not result:
                return
        
        # Destroy window if exists
        if self.window:
            self.window.destroy()
        
        # Call quit callback
        if self.quit_callback:
            self.quit_callback()

# =============================================================================
# TRAY APPLICATION
# =============================================================================

class TrayApp:
    """Main tray application"""
    
    def __init__(self):
        self.server_mgr = ServerManager()
        self.gui_mgr = None
        self.icon = None
        self.running = True
    
    def setup(self):
        """Setup the application"""
        # Create lock file
        self._create_lock_file()
        
        # Setup GUI manager
        self.gui_mgr = GUIManager(self.server_mgr, self.quit)
        
        # Load tray icon image
        icon_image = self._load_icon()
        
        # Create tray icon
        menu = pystray.Menu(
            item('Open Control Panel', self._show_gui, default=True),
            item('Open in Browser', self._open_browser),
            pystray.Menu.SEPARATOR,
            item('Start Server', self._start_server, visible=lambda _: not self.server_mgr.is_running()),
            item('Stop Server', self._stop_server, visible=lambda _: self.server_mgr.is_running()),
            pystray.Menu.SEPARATOR,
            item('Start with Windows', self._toggle_autostart, checked=lambda _: self._is_autostart_enabled()),
            pystray.Menu.SEPARATOR,
            item('Quit', self._quit_from_menu)
        )
        
        self.icon = pystray.Icon(
            "label_print_server",
            icon_image,
            "Label Print Server",
            menu
        )
        
        # Start server
        self.server_mgr.start()
    
    def _load_icon(self):
        """Load the tray icon image"""
        icon_path = APP_DIR / 'icons' / 'app_icon.ico'
        if icon_path.exists():
            try:
                return PIL.Image.open(str(icon_path))
            except:
                pass
        
        # Create a simple default icon
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (64, 64), color='#2c3e50')
        draw = ImageDraw.Draw(img)
        draw.rectangle([16, 16, 48, 48], fill='#3498db')
        return img
    
    def _create_lock_file(self):
        """Create lock file"""
        try:
            LOCK_FILE.write_text(str(os.getpid()))
            print(f"Created lock file (PID {os.getpid()})")
        except Exception as e:
            print(f"Error creating lock file: {e}")
    
    def _cleanup_lock_file(self):
        """Remove lock file"""
        try:
            if LOCK_FILE.exists():
                LOCK_FILE.unlink()
                print("Removed lock file")
        except Exception as e:
            print(f"Error removing lock file: {e}")
    
    def _show_gui(self, icon=None, item=None):
        """Show the GUI control panel"""
        self.gui_mgr.show()
    
    def _open_browser(self, icon=None, item=None):
        """Open browser"""
        webbrowser.open(f"http://localhost:{SERVER_PORT}")
    
    def _start_server(self, icon=None, item=None):
        """Start server"""
        self.server_mgr.start()
        if self.icon:
            self.icon.update_menu()
    
    def _stop_server(self, icon=None, item=None):
        """Stop server"""
        self.server_mgr.stop()
        if self.icon:
            self.icon.update_menu()
    
    def _is_autostart_enabled(self):
        """Check if auto-start is enabled in registry"""
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            try:
                value, _ = winreg.QueryValueEx(key, "LabelPrintServer")
                winreg.CloseKey(key)
                return bool(value)
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except:
            return False
    
    def _toggle_autostart(self, icon=None, item=None):
        """Toggle auto-start on/off"""
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            if self._is_autostart_enabled():
                # Disable auto-start
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                try:
                    winreg.DeleteValue(key, "LabelPrintServer")
                    print("Auto-start disabled")
                except:
                    pass
                winreg.CloseKey(key)
            else:
                # Enable auto-start
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                vbs_launcher = APP_DIR / 'startup_launcher.vbs'
                value = f'wscript.exe "{vbs_launcher}"'
                winreg.SetValueEx(key, "LabelPrintServer", 0, winreg.REG_SZ, value)
                winreg.CloseKey(key)
                print("Auto-start enabled")
            
            # Update menu to reflect new state
            if self.icon:
                self.icon.update_menu()
                
        except Exception as e:
            print(f"Error toggling auto-start: {e}")
            if self.gui_mgr and self.gui_mgr.root:
                messagebox.showerror("Auto-start Error", f"Failed to toggle auto-start:\n{e}")
    
    def _quit_from_menu(self, icon=None, item=None):
        """Quit from tray menu"""
        self.quit()
    
    def quit(self):
        """Quit the application"""
        print("Quitting application...")
        self.running = False
        
        # Stop server
        self.server_mgr.stop()
        
        # Destroy GUI window
        if self.gui_mgr and self.gui_mgr.window:
            try:
                self.gui_mgr.window.destroy()
            except:
                pass
        
        # Stop tray icon
        if self.icon:
            self.icon.stop()
        
        # Destroy root window
        if self.gui_mgr and self.gui_mgr.root:
            try:
                self.gui_mgr.root.quit()
            except:
                pass
        
        # Cleanup
        self._cleanup_lock_file()
        
        # Exit
        sys.exit(0)
    
    def run(self):
        """Run the application"""
        print("=" * 60)
        print("Label Print Server - Tray Application")
        print("=" * 60)
        
        # Check single instance
        if not self._check_single_instance():
            print("Another instance is already running!")
            sys.exit(1)
        
        # Setup
        self.setup()
        
        # Run tray icon in separate thread
        print("Tray app running. Click icon for menu.")
        tray_thread = threading.Thread(target=self.icon.run, daemon=False)
        tray_thread.start()
        
        # Run Tkinter main loop in main thread
        # Create a hidden root window for event loop
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        
        # Make sure GUI manager uses this root
        self.gui_mgr.root = root
        
        try:
            root.mainloop()
        except KeyboardInterrupt:
            print("\nKeyboard interrupt")
            self.quit()
    
    def _check_single_instance(self):
        """Ensure only one instance is running"""
        if LOCK_FILE.exists():
            try:
                pid = int(LOCK_FILE.read_text().strip())
                
                # Check if process exists
                try:
                    import ctypes
                    handle = ctypes.windll.kernel32.OpenProcess(0x400, False, pid)
                    if handle:
                        ctypes.windll.kernel32.CloseHandle(handle)
                        return False  # Another instance running
                except:
                    pass
                
                # Stale lock file
                print(f"Removing stale lock file (PID {pid})")
                LOCK_FILE.unlink()
            except Exception as e:
                print(f"Error checking lock file: {e}")
                try:
                    LOCK_FILE.unlink()
                except:
                    pass
        
        return True

# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point"""
    app = TrayApp()
    app.run()

if __name__ == "__main__":
    main()
