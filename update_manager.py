"""
Auto-Update System for Label Print Server
Checks GitHub releases and handles automatic updates
"""

import os
import sys
import json
import requests
import zipfile
import tempfile
import shutil
import subprocess
import threading
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import winreg
from packaging import version

class UpdateManager:
    def __init__(self):
        self.github_repo = "goks/Label-print-server"  # Update with your actual repo
        self.current_version = self.get_current_version()
        self.app_dir = Path(__file__).parent.absolute()
        self.update_config_file = self.app_dir / "update_config.json"
        self.update_log_file = self.app_dir / "logs" / "updates.log"
        
        # Ensure logs directory exists
        self.update_log_file.parent.mkdir(exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger('UpdateManager')
        handler = logging.FileHandler(self.update_log_file)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Load or create update configuration
        self.config = self.load_update_config()
    
    def get_current_version(self):
        """Get current application version"""
        try:
            # Try to read from version file first
            version_file = Path(__file__).parent / "VERSION"
            if version_file.exists():
                return version_file.read_text().strip()
            
            # Try to read from CHANGELOG.md
            changelog_file = Path(__file__).parent / "CHANGELOG.md"
            if changelog_file.exists():
                content = changelog_file.read_text()
                # Look for version pattern like ## [2.0.0] or # v2.0.0
                import re
                version_match = re.search(r'##?\s*\[?v?(\d+\.\d+\.\d+)\]?', content)
                if version_match:
                    return version_match.group(1)
            
            # Fallback to default version
            return "2.0.0"
        except Exception as e:
            self.logger.warning(f"Could not determine version: {e}")
            return "2.0.0"
    
    def load_update_config(self):
        """Load update configuration"""
        default_config = {
            "auto_check": True,
            "auto_install": False,  # Manual approval by default
            "check_interval_hours": 24,
            "last_check": None,
            "update_channel": "stable",  # stable, beta, all
            "backup_enabled": True,
            "notification_enabled": True
        }
        
        try:
            if self.update_config_file.exists():
                with open(self.update_config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults for new settings
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
        
        return default_config
    
    def save_update_config(self):
        """Save update configuration"""
        try:
            with open(self.update_config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
    
    def check_for_updates(self, force=False):
        """Check GitHub for new releases"""
        try:
            # Check if enough time has passed since last check
            if not force and self.config.get("last_check"):
                last_check = datetime.fromisoformat(self.config["last_check"])
                next_check = last_check + timedelta(hours=self.config["check_interval_hours"])
                if datetime.now() < next_check:
                    self.logger.info("Update check skipped - too soon since last check")
                    return None
            
            self.logger.info("Checking for updates...")
            
            # Get latest release from GitHub API
            api_url = f"https://api.github.com/repos/{self.github_repo}/releases"
            
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            
            releases = response.json()
            
            if not releases:
                self.logger.info("No releases found")
                return None
            
            # Filter releases based on update channel
            filtered_releases = self.filter_releases_by_channel(releases)
            
            if not filtered_releases:
                self.logger.info(f"No releases found for channel: {self.config['update_channel']}")
                return None
            
            latest_release = filtered_releases[0]
            latest_version = latest_release["tag_name"].lstrip('v')
            
            # Update last check time
            self.config["last_check"] = datetime.now().isoformat()
            self.save_update_config()
            
            # Compare versions
            if version.parse(latest_version) > version.parse(self.current_version):
                update_info = {
                    "version": latest_version,
                    "release": latest_release,
                    "download_url": self.get_download_url(latest_release),
                    "changelog": latest_release.get("body", ""),
                    "published_at": latest_release["published_at"],
                    "is_prerelease": latest_release["prerelease"]
                }
                
                self.logger.info(f"Update available: {latest_version}")
                return update_info
            else:
                self.logger.info(f"No update needed. Current: {self.current_version}, Latest: {latest_version}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")
            return None
    
    def filter_releases_by_channel(self, releases):
        """Filter releases based on update channel"""
        if self.config["update_channel"] == "stable":
            return [r for r in releases if not r["prerelease"]]
        elif self.config["update_channel"] == "beta":
            return [r for r in releases if r["prerelease"]]
        else:  # all
            return releases
    
    def get_download_url(self, release):
        """Get download URL for the release"""
        # Look for Windows zip file in assets
        for asset in release.get("assets", []):
            if asset["name"].endswith(".zip") and ("windows" in asset["name"].lower() or "win" in asset["name"].lower()):
                return asset["browser_download_url"]
        
        # Fallback to source code zip
        return release["zipball_url"]
    
    def download_update(self, update_info, progress_callback=None):
        """Download update package"""
        try:
            download_url = update_info["download_url"]
            version_str = update_info["version"]
            
            self.logger.info(f"Downloading update {version_str} from {download_url}")
            
            # Create temporary download directory
            temp_dir = Path(tempfile.gettempdir()) / f"label_print_server_update_{version_str}"
            temp_dir.mkdir(exist_ok=True)
            
            download_path = temp_dir / f"update_{version_str}.zip"
            
            # Download with progress
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            progress_callback(progress)
            
            self.logger.info(f"Update downloaded to {download_path}")
            return download_path
            
        except Exception as e:
            self.logger.error(f"Error downloading update: {e}")
            raise
    
    def create_backup(self):
        """Create backup of current installation"""
        if not self.config["backup_enabled"]:
            return None
        
        try:
            backup_dir = self.app_dir / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{self.current_version}_{timestamp}.zip"
            backup_path = backup_dir / backup_name
            
            self.logger.info(f"Creating backup: {backup_path}")
            
            # Files to backup (exclude logs, temp files, etc.)
            backup_files = [
                "app.py", "wsgi.py", "tray_app.py", "tray_gui.py",
                "service_manager.py", "auto_startup.py", "printed_db.py",
                "requirements.txt", "templates/", "icons/",
                ".env", "db_settings.json", "update_config.json"
            ]
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                for file_pattern in backup_files:
                    file_path = self.app_dir / file_pattern
                    if file_path.exists():
                        if file_path.is_file():
                            backup_zip.write(file_path, file_path.name)
                        elif file_path.is_dir():
                            for sub_file in file_path.rglob("*"):
                                if sub_file.is_file():
                                    arcname = str(sub_file.relative_to(self.app_dir))
                                    backup_zip.write(sub_file, arcname)
            
            # Keep only last 5 backups
            self.cleanup_old_backups(backup_dir, keep=5)
            
            self.logger.info(f"Backup created successfully: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return None
    
    def cleanup_old_backups(self, backup_dir, keep=5):
        """Clean up old backup files"""
        try:
            backup_files = list(backup_dir.glob("backup_*.zip"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for old_backup in backup_files[keep:]:
                old_backup.unlink()
                self.logger.info(f"Deleted old backup: {old_backup}")
        except Exception as e:
            self.logger.error(f"Error cleaning up backups: {e}")
    
    def install_update(self, download_path, update_info):
        """Install the downloaded update"""
        try:
            version_str = update_info["version"]
            self.logger.info(f"Installing update {version_str}")
            
            # Create backup before installing
            backup_path = self.create_backup()
            
            # Extract update
            temp_extract_dir = Path(tempfile.gettempdir()) / f"extract_{version_str}"
            temp_extract_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_dir)
            
            # Find the actual application files in the extracted directory
            app_files_dir = self.find_app_files_directory(temp_extract_dir)
            
            if not app_files_dir:
                raise Exception("Could not find application files in update package")
            
            # Stop services before update
            self.stop_services()
            
            # Install files (preserve user config)
            self.install_files(app_files_dir)
            
            # Update version file
            version_file = self.app_dir / "VERSION"
            version_file.write_text(version_str)
            
            # Update dependencies
            self.update_dependencies()
            
            # Start services
            self.start_services()
            
            self.logger.info(f"Update {version_str} installed successfully")
            
            # Clean up
            shutil.rmtree(temp_extract_dir, ignore_errors=True)
            download_path.unlink(missing_ok=True)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error installing update: {e}")
            # Attempt to restore from backup if available
            if backup_path and backup_path.exists():
                self.logger.info("Attempting to restore from backup...")
                try:
                    self.restore_from_backup(backup_path)
                except Exception as restore_error:
                    self.logger.error(f"Failed to restore from backup: {restore_error}")
            raise
    
    def find_app_files_directory(self, extract_dir):
        """Find the directory containing application files"""
        # Look for main app files
        for root, dirs, files in os.walk(extract_dir):
            if "app.py" in files and "wsgi.py" in files:
                return Path(root)
        return None
    
    def install_files(self, source_dir):
        """Install files from source directory to application directory"""
        # Files to update (preserve user configurations)
        update_files = [
            "app.py", "wsgi.py", "tray_app.py", "tray_gui.py",
            "service_manager.py", "auto_startup.py", "printed_db.py",
            "requirements.txt", "templates/", "icons/", "static/"
        ]
        
        preserve_files = [
            ".env", "db_settings.json", "update_config.json",
            "logs/", "backups/", ".tray_running", "printed_records.db"
        ]
        
        for file_pattern in update_files:
            source_path = source_dir / file_pattern
            target_path = self.app_dir / file_pattern
            
            if source_path.exists():
                if source_path.is_file():
                    # Copy file
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_path, target_path)
                elif source_path.is_dir():
                    # Copy directory
                    if target_path.exists():
                        shutil.rmtree(target_path)
                    shutil.copytree(source_path, target_path)
    
    def update_dependencies(self):
        """Update Python dependencies"""
        try:
            requirements_file = self.app_dir / "requirements.txt"
            if requirements_file.exists():
                venv_python = self.app_dir / ".venv" / "Scripts" / "python.exe"
                if venv_python.exists():
                    subprocess.run([
                        str(venv_python), "-m", "pip", "install", "-r", 
                        str(requirements_file), "--upgrade"
                    ], check=True, capture_output=True)
                    self.logger.info("Dependencies updated successfully")
        except Exception as e:
            self.logger.error(f"Error updating dependencies: {e}")
    
    def stop_services(self):
        """Stop running services before update"""
        try:
            # Signal tray app to quit
            quit_signal_file = self.app_dir / ".tray_quit_signal"
            quit_signal_file.touch()
            
            # Wait a moment for graceful shutdown
            time.sleep(2)
            
            # Force kill if still running
            subprocess.run(["taskkill", "/F", "/IM", "python.exe"], 
                          capture_output=True, check=False)
            
            self.logger.info("Services stopped for update")
        except Exception as e:
            self.logger.error(f"Error stopping services: {e}")
    
    def start_services(self):
        """Start services after update"""
        try:
            # Check if auto-startup is enabled
            if self.is_auto_startup_enabled():
                # Services will start on next boot, or user can start manually
                self.logger.info("Auto-startup is enabled - services will start automatically")
            else:
                self.logger.info("Manual startup required after update")
        except Exception as e:
            self.logger.error(f"Error starting services: {e}")
    
    def is_auto_startup_enabled(self):
        """Check if auto-startup is enabled"""
        try:
            startup_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            app_name = "Label Print Server"
            
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, startup_key, 0, winreg.KEY_READ) as key:
                winreg.QueryValueEx(key, app_name)
                return True
        except FileNotFoundError:
            return False
    
    def restore_from_backup(self, backup_path):
        """Restore from backup in case of update failure"""
        try:
            self.logger.info(f"Restoring from backup: {backup_path}")
            
            with zipfile.ZipFile(backup_path, 'r') as backup_zip:
                backup_zip.extractall(self.app_dir)
            
            self.logger.info("Backup restored successfully")
        except Exception as e:
            self.logger.error(f"Error restoring backup: {e}")
            raise
    
    def check_and_update(self, force=False, auto_install=None):
        """Main method to check for updates and optionally install"""
        try:
            # Check for updates
            update_info = self.check_for_updates(force)
            
            if not update_info:
                return {"status": "no_update", "message": "No updates available"}
            
            # Determine if we should auto-install
            should_auto_install = (
                auto_install if auto_install is not None 
                else self.config.get("auto_install", False)
            )
            
            if should_auto_install:
                # Download and install automatically
                self.logger.info("Auto-installing update...")
                
                def progress_callback(progress):
                    self.logger.info(f"Download progress: {progress:.1f}%")
                
                download_path = self.download_update(update_info, progress_callback)
                self.install_update(download_path, update_info)
                
                return {
                    "status": "updated",
                    "version": update_info["version"],
                    "message": f"Updated to version {update_info['version']}"
                }
            else:
                # Notify about available update
                return {
                    "status": "update_available",
                    "version": update_info["version"],
                    "changelog": update_info["changelog"],
                    "published_at": update_info["published_at"],
                    "message": f"Update {update_info['version']} is available"
                }
                
        except Exception as e:
            self.logger.error(f"Error in check_and_update: {e}")
            return {"status": "error", "message": str(e)}
    
    def manual_update(self, version=None):
        """Manually trigger update installation"""
        try:
            update_info = self.check_for_updates(force=True)
            
            if not update_info:
                return {"status": "no_update", "message": "No updates available"}
            
            # Download and install
            download_path = self.download_update(update_info)
            self.install_update(download_path, update_info)
            
            return {
                "status": "success",
                "version": update_info["version"],
                "message": f"Successfully updated to version {update_info['version']}"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Background update checker
class UpdateChecker:
    def __init__(self, update_manager):
        self.update_manager = update_manager
        self.running = False
        self.thread = None
    
    def start(self):
        """Start background update checking"""
        if self.update_manager.config.get("auto_check", True):
            self.running = True
            self.thread = threading.Thread(target=self._check_loop, daemon=True)
            self.thread.start()
    
    def stop(self):
        """Stop background update checking"""
        self.running = False
    
    def _check_loop(self):
        """Background update check loop"""
        while self.running:
            try:
                # Check for updates
                result = self.update_manager.check_and_update()
                
                # Log results
                if result["status"] == "update_available":
                    self.update_manager.logger.info(f"Update available: {result['version']}")
                
                # Wait for next check (check every hour, but respect config)
                interval = self.update_manager.config.get("check_interval_hours", 24)
                sleep_time = min(interval * 3600, 3600)  # Max 1 hour sleep
                
                for _ in range(int(sleep_time)):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.update_manager.logger.error(f"Background update check error: {e}")
                time.sleep(600)  # Wait 10 minutes on error

# CLI interface
def main():
    """Command line interface for update management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Label Print Server Update Manager")
    parser.add_argument("command", choices=["check", "update", "config", "status"], 
                       help="Command to execute")
    parser.add_argument("--force", action="store_true", help="Force check even if recently checked")
    parser.add_argument("--auto-install", action="store_true", help="Automatically install updates")
    parser.add_argument("--channel", choices=["stable", "beta", "all"], help="Update channel")
    
    args = parser.parse_args()
    
    update_manager = UpdateManager()
    
    if args.channel:
        update_manager.config["update_channel"] = args.channel
        update_manager.save_update_config()
    
    if args.command == "check":
        print("🔍 Checking for updates...")
        result = update_manager.check_and_update(force=args.force, auto_install=args.auto_install)
        print(f"📊 Result: {result}")
        
    elif args.command == "update":
        print("📦 Manually updating...")
        result = update_manager.manual_update()
        print(f"📊 Result: {result}")
        
    elif args.command == "config":
        print("⚙️ Current Configuration:")
        for key, value in update_manager.config.items():
            print(f"  {key}: {value}")
            
    elif args.command == "status":
        print(f"📋 Label Print Server Update Status:")
        print(f"  Current Version: {update_manager.current_version}")
        print(f"  Auto Check: {update_manager.config['auto_check']}")
        print(f"  Auto Install: {update_manager.config['auto_install']}")
        print(f"  Update Channel: {update_manager.config['update_channel']}")
        print(f"  Last Check: {update_manager.config.get('last_check', 'Never')}")

if __name__ == "__main__":
    main()