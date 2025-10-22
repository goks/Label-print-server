import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk
import webbrowser
import requests
import os
import sys
import json
import tempfile


# Simple standalone GUI for controlling the Label Print Server
class TrayGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Label Print Server")
        self.geometry("700x400")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Save window handle for tray restoration
        self.save_window_info()
        
        # Start checking for restore signals
        self.after(1000, self.check_restore_signal)

        top_frame = tk.Frame(self)
        top_frame.pack(fill='x', padx=8, pady=6)

        self.status_label = tk.Label(top_frame, text="Server Status: Checking...")
        self.status_label.pack(side='left')

        self.start_btn = tk.Button(top_frame, text="Start Server", command=self.start_server)
        self.start_btn.pack(side='left', padx=6)

        self.stop_btn = tk.Button(top_frame, text="Stop Server", command=self.stop_server)
        self.stop_btn.pack(side='left', padx=6)

        open_browser_btn = tk.Button(top_frame, text="Open in Browser", command=self.open_browser)
        open_browser_btn.pack(side='left', padx=6)

        # Minimize to tray (previously Exit)
        self.minimize_btn = tk.Button(top_frame, text="Minimize to Tray", command=self.minimize_to_tray)
        self.minimize_btn.pack(side='right', padx=6)

        # Quit button (warn if server running)
        self.quit_btn = tk.Button(top_frame, text="Quit", command=self.quit_requested)
        self.quit_btn.pack(side='right', padx=6)

        # Add search and table area
        search_frame = tk.Frame(self)
        search_frame.pack(fill='x', padx=8)

        tk.Label(search_frame, text='Search Quotation:').pack(side='left')
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side='left', padx=6)
        # Debounced dynamic search while typing
        self._search_after_id = None
        def on_key_release(event=None):
            # reset to first page and debounce
            if self._search_after_id:
                try:
                    self.after_cancel(self._search_after_id)
                except Exception:
                    pass
            self.current_page = 1
            # schedule reload after 400ms
            self._search_after_id = self.after(400, lambda: self.reload_table(query=self.search_var.get().strip(), page=self.current_page))

        search_entry.bind('<KeyRelease>', on_key_release)

        search_btn = tk.Button(search_frame, text='Search', command=self.on_search)
        search_btn.pack(side='left')

        reload_btn = tk.Button(search_frame, text='Reload', command=lambda: self.reload_table(query=self.search_var.get().strip(), page=self.current_page))
        reload_btn.pack(side='left', padx=6)

        # Table
        # Show printed_at immediately after id for readability
        cols = ('id','printed_at','quotation','party','address','phone','mobile')
        self.tree = ttk.Treeview(self, columns=cols, show='headings')
        # sensible widths
        widths = {'id':50, 'printed_at':140, 'quotation':90, 'party':180, 'address':260, 'phone':110, 'mobile':110}
        for col in cols:
            # Title-case with spaces
            title = ' '.join([p.capitalize() for p in col.split('_')])
            self.tree.heading(col, text=title)
            self.tree.column(col, width=widths.get(col,100), anchor='w')
        self.tree.pack(fill='both', expand=True, padx=8, pady=6)
        # double click to show details
        self.tree.bind('<Double-1>', self.on_row_double)
        # Pagination state
        self.current_page = 1
        self.page_size = 50

        # Controls for pagination and export
        ctrl_frame = tk.Frame(self)
        ctrl_frame.pack(fill='x', padx=8, pady=(0,6))

        self.prev_btn = tk.Button(ctrl_frame, text='<< Prev', command=self.on_prev)
        self.prev_btn.pack(side='left')
        self.page_label = tk.Label(ctrl_frame, text='Page 1')
        self.page_label.pack(side='left', padx=6)
        self.next_btn = tk.Button(ctrl_frame, text='Next >>', command=self.on_next)
        self.next_btn.pack(side='left')

        export_btn = tk.Button(ctrl_frame, text='Export CSV', command=self.export_csv)
        export_btn.pack(side='right')
        copy_btn = tk.Button(ctrl_frame, text='Copy Selected', command=self.copy_selected)
        copy_btn.pack(side='right', padx=6)

        # Start periodic update
        self.after(1000, self.update_status)
        self.after(2000, self.reload_table_periodic)

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
                
                # Restore window
                self.deiconify()
                self.lift()
                self.focus_force()
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
                    # format printed_at nicely if ISO
                    printed_at = rec.get('printed_at')
                    try:
                        # try parsing ISO format
                        from datetime import datetime
                        dt = datetime.fromisoformat(printed_at)
                        printed_at_str = dt.strftime('%Y-%m-%d %H:%M:%S')
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

    def on_close(self):
        self.destroy()


if __name__ == '__main__':
    app = TrayGUI()
    app.mainloop()
