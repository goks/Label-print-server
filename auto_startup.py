"""
Auto-Startup Installer for Label Print Server
Configures the application to start automatically with Windows
"""
import os
import sys
import winreg
import shutil
from pathlib import Path

class AutoStartupManager:
    def __init__(self):
        self.app_dir = Path(__file__).parent.absolute()
        self.app_name = "Label Print Server"
        self.startup_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        
    def install_startup(self):
        """Install the application to start with Windows"""
        print(f"Installing {self.app_name} for auto-startup...")
        
        # Create the startup command using VBS for silent execution
        vbs_file = self.app_dir / "start_tray_silent.vbs"
        if not vbs_file.exists():
            print("Error: start_tray_silent.vbs not found!")
            return False
            
        startup_command = f'wscript.exe "{vbs_file}"'
        
        try:
            # Open the registry key for startup programs
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.startup_key, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, startup_command)
            
            print(f"✅ {self.app_name} installed for auto-startup")
            print(f"   Command: {startup_command}")
            print(f"   Location: HKEY_CURRENT_USER\\{self.startup_key}")
            print("\n🔄 The tray application will start automatically on next boot")
            print("💡 You can also start it now by running: start_tray_silent.vbs")
            return True
            
        except Exception as e:
            print(f"❌ Error installing auto-startup: {e}")
            return False
    
    def uninstall_startup(self):
        """Remove the application from Windows startup"""
        print(f"Removing {self.app_name} from auto-startup...")
        
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.startup_key, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, self.app_name)
            
            print(f"✅ {self.app_name} removed from auto-startup")
            return True
            
        except FileNotFoundError:
            print(f"ℹ️ {self.app_name} was not configured for auto-startup")
            return True
        except Exception as e:
            print(f"❌ Error removing auto-startup: {e}")
            return False
    
    def check_startup_status(self):
        """Check if the application is configured for auto-startup"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.startup_key, 0, winreg.KEY_READ) as key:
                value, reg_type = winreg.QueryValueEx(key, self.app_name)
                print(f"✅ {self.app_name} is configured for auto-startup")
                print(f"   Command: {value}")
                return True
        except FileNotFoundError:
            print(f"❌ {self.app_name} is not configured for auto-startup")
            return False
        except Exception as e:
            print(f"❓ Error checking startup status: {e}")
            return False
    
    def create_desktop_shortcut(self):
        """Create a desktop shortcut for manual startup"""
        try:
            import win32com.client
            
            desktop = Path.home() / "Desktop"
            shortcut_path = desktop / f"{self.app_name}.lnk"
            vbs_file = self.app_dir / "start_tray_silent.vbs"
            
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.Targetpath = "wscript.exe"
            shortcut.Arguments = f'"{vbs_file}"'
            shortcut.WorkingDirectory = str(self.app_dir)
            shortcut.Description = f"Start {self.app_name} in system tray"
            
            # Try to set icon
            icon_file = self.app_dir / "icons" / "favicon.ico"
            if icon_file.exists():
                shortcut.IconLocation = str(icon_file)
            
            shortcut.save()
            print(f"✅ Desktop shortcut created: {shortcut_path}")
            return True
            
        except ImportError:
            print("⚠️ Could not create desktop shortcut (pywin32 not available)")
            print(f"💡 You can manually create a shortcut to: {self.app_dir / 'start_tray_silent.vbs'}")
            return False
        except Exception as e:
            print(f"❌ Error creating desktop shortcut: {e}")
            return False

def main():
    if len(sys.argv) < 2:
        print("=" * 50)
        print("    Label Print Server - Auto-Startup Manager")
        print("=" * 50)
        print("\n📋 Available Commands:")
        print("  python auto_startup.py install    # Configure auto-startup on boot")
        print("  python auto_startup.py uninstall  # Remove auto-startup")  
        print("  python auto_startup.py status     # Check current status")
        print("  python auto_startup.py shortcut   # Create desktop shortcut")
        print("  python auto_startup.py setup      # Complete setup (install + shortcut)")
        print("  python auto_startup.py menu       # Interactive menu")
        print("\n💡 Quick Options:")
        print("  • For complete setup: python auto_startup.py setup")
        print("  • For removal: remove_startup.bat")
        print("  • For interactive mode: python auto_startup.py menu")
        return
    
    manager = AutoStartupManager()
    command = sys.argv[1].lower()
    
    if command == "install":
        success = manager.install_startup()
        if success:
            print("\n🎉 Setup complete! The Label Print Server will start automatically with Windows.")
        
    elif command == "uninstall":
        manager.uninstall_startup()
        
    elif command == "status":
        manager.check_startup_status()
        
    elif command == "shortcut":
        manager.create_desktop_shortcut()
        
    elif command == "setup":
        print("=== Label Print Server Auto-Startup Setup ===\n")
        
        # Install auto-startup
        if manager.install_startup():
            print()
            # Create desktop shortcut
            manager.create_desktop_shortcut()
            print("\n🎉 Complete setup finished!")
            print("\n📋 What happens now:")
            print("   • Tray icon will appear automatically on Windows startup")
            print("   • Server runs in background when tray icon is present")
            print("   • Use desktop shortcut for manual startup")
            print("   • Access web interface at: http://localhost:5000")
            
    elif command == "menu":
        show_interactive_menu(manager)
        
    else:
        print(f"Unknown command: {command}")
        print("Use 'python auto_startup.py' for usage information")

def show_interactive_menu(manager):
    """Show interactive menu for auto-startup management"""
    while True:
        print("\n" + "=" * 50)
        print("    Label Print Server - Auto-Startup Manager")
        print("=" * 50)
        
        # Check current status
        print("\n📊 Current Status:")
        is_configured = manager.check_startup_status()
        
        print("\n📋 Available Options:")
        if not is_configured:
            print("  1. ✅ Install auto-startup (start with Windows)")
            print("  2. 🖥️ Create desktop shortcut")
            print("  3. 🚀 Complete setup (install + shortcut)")
        else:
            print("  1. ❌ Remove auto-startup")
            print("  2. 🖥️ Create/update desktop shortcut")
            print("  3. 🔄 Reinstall auto-startup")
        
        print("  4. 📊 Check status")
        print("  5. ❓ Help")
        print("  0. 🚪 Exit")
        
        choice = input("\n👆 Enter your choice (0-5): ").strip()
        
        if choice == "0":
            print("\n👋 Goodbye!")
            break
        elif choice == "1":
            if not is_configured:
                manager.install_startup()
            else:
                confirm = input("\n⚠️  Remove auto-startup? Type 'yes' to confirm: ").strip().lower()
                if confirm == "yes":
                    manager.uninstall_startup()
                else:
                    print("❌ Operation cancelled")
        elif choice == "2":
            manager.create_desktop_shortcut()
        elif choice == "3":
            if not is_configured:
                print("\n🚀 Running complete setup...")
                if manager.install_startup():
                    manager.create_desktop_shortcut()
                    print("\n🎉 Complete setup finished!")
            else:
                print("\n🔄 Reinstalling auto-startup...")
                manager.uninstall_startup()
                manager.install_startup()
        elif choice == "4":
            print("\n📊 Checking status...")
            manager.check_startup_status()
        elif choice == "5":
            show_help()
        else:
            print("❌ Invalid choice. Please enter 0-5.")

def show_help():
    """Show help information"""
    print("\n" + "=" * 50)
    print("    📖 Help - Auto-Startup Manager")
    print("=" * 50)
    print("\n🎯 Purpose:")
    print("   Configure Label Print Server to start automatically with Windows")
    print("   and appear as a tray icon for easy access.")
    
    print("\n⚙️ How It Works:")
    print("   • Adds registry entry to Windows startup")
    print("   • Uses silent VBS script (no console window)")
    print("   • Starts tray application with embedded server")
    print("   • Server available at http://localhost:5000")
    
    print("\n📁 Files Created:")
    print("   • Registry: HKEY_CURRENT_USER\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run")
    print("   • Shortcut: Desktop\\Label Print Server.lnk")
    
    print("\n🔧 Manual Control:")
    print("   • Start: start_tray_silent.vbs")
    print("   • Remove: remove_startup.bat")
    print("   • Status: python auto_startup.py status")
    
    print("\n🆘 Troubleshooting:")
    print("   • If tray doesn't appear: Check Windows notifications")
    print("   • If server doesn't start: Check .env configuration")
    print("   • For errors: Check logs/ directory")
    
    input("\nPress Enter to return to menu...")

if __name__ == "__main__":
    main()