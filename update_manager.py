"""
GitHub release updater for Label Print Server.

This updater is designed for the installed tray application:
- checks GitHub releases for a newer EXE asset
- downloads the EXE to a temp folder
- stages a small updater script to replace the running EXE after exit
- relaunches the application automatically
"""

import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import re
from datetime import datetime, timedelta
from pathlib import Path

import requests
from packaging import version
from packaging.version import InvalidVersion


DEFAULT_GITHUB_REPO = "goks/Label-print-server"
DEFAULT_INSTALLER_NAME = "LabelPrintServer_Setup.exe"


class UpdateManager:
    def __init__(self):
        self.app_dir = Path(__file__).parent.absolute()
        self.data_dir = self._get_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir = self.data_dir / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir = self.data_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self.update_config_file = self.data_dir / "update_config.json"
        self.logger = logging.getLogger("UpdateManager")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        self._ensure_logger_handler()

        self.current_version = self.get_current_version()
        self.config = self.load_update_config()
        self.github_repo = self.config.get("github_repo", DEFAULT_GITHUB_REPO)

    def _get_data_dir(self):
        """Return a writable application data directory."""
        if "Program Files" in str(self.app_dir):
            return Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))) / "LabelPrintServer"
        return self.app_dir

    def _ensure_logger_handler(self):
        """Attach a single file handler even across repeated imports."""
        log_file = self.log_dir / "updates.log"
        log_path = str(log_file)

        for handler in self.logger.handlers[:]:
            if isinstance(handler, logging.FileHandler) and getattr(handler, "baseFilename", None) == log_path:
                return
            self.logger.removeHandler(handler)

        handler = logging.FileHandler(log_file, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(handler)

    def get_current_version(self):
        """Get the current application version."""
        try:
            version_file = self.app_dir / "VERSION"
            if version_file.exists():
                return version_file.read_text(encoding="utf-8").strip()
        except Exception:
            pass
        return "0.0.0"

    def load_update_config(self):
        """Load updater configuration."""
        default_config = {
            "auto_check": True,
            "auto_install": False,
            "check_interval_hours": 24,
            "last_check": None,
            "last_notified_version": None,
            "update_channel": "stable",
            "backup_enabled": True,
            "notification_enabled": True,
            "github_repo": DEFAULT_GITHUB_REPO,
            "asset_name_contains": "LabelPrintServer_Setup",
        }

        try:
            if self.update_config_file.exists():
                with open(self.update_config_file, "r", encoding="utf-8") as file_obj:
                    config = json.load(file_obj)
                merged = default_config.copy()
                merged.update(config)
                if merged.get("asset_name_contains") == "LabelPrintServer":
                    merged["asset_name_contains"] = "LabelPrintServer_Setup"
                return merged
        except Exception as exc:
            self.logger.error("Error loading update config: %s", exc)

        return default_config

    def save_update_config(self):
        """Persist updater configuration."""
        with open(self.update_config_file, "w", encoding="utf-8") as file_obj:
            json.dump(self.config, file_obj, indent=2)

    def should_notify_for(self, version_str):
        """Return True if the user has not already been notified for this version."""
        if not self.config.get("notification_enabled", True):
            return False
        return self.config.get("last_notified_version") != version_str

    def mark_notified(self, version_str):
        """Persist the last version the user has been notified about."""
        self.config["last_notified_version"] = version_str
        self.save_update_config()

    def check_for_updates(self, force=False):
        """Check GitHub releases for a newer installer build."""
        try:
            if not force and self.config.get("last_check"):
                last_check = datetime.fromisoformat(self.config["last_check"])
                next_check = last_check + timedelta(hours=self.config.get("check_interval_hours", 24))
                if datetime.now() < next_check:
                    self.logger.info("Skipping update check because interval has not elapsed yet")
                    return None

            releases = self._fetch_releases()
            if not releases:
                self._record_check()
                return None

            filtered_releases = self.filter_releases_by_channel(releases)
            if not filtered_releases:
                self._record_check()
                return None

            latest_release = filtered_releases[0]
            latest_version = latest_release["tag_name"].lstrip("v")

            self._record_check()

            if self._parse_version_for_compare(latest_version) <= self._parse_version_for_compare(self.current_version):
                self.logger.info(
                    "No update needed. Current=%s Latest=%s",
                    self.current_version,
                    latest_version,
                )
                return None

            asset = self._select_release_asset(latest_release)
            if not asset:
                raise RuntimeError("Latest release does not contain a downloadable installer asset")

            update_info = {
                "version": latest_version,
                "release_name": latest_release.get("name") or latest_release["tag_name"],
                "download_url": asset["browser_download_url"],
                "asset_name": asset["name"],
                "asset_size": asset.get("size", 0),
                "published_at": latest_release.get("published_at"),
                "changelog": latest_release.get("body") or "No release notes provided.",
                "html_url": latest_release.get("html_url"),
                "is_prerelease": latest_release.get("prerelease", False),
            }

            self.logger.info("Update available: %s (%s)", update_info["version"], update_info["asset_name"])
            return update_info
        except Exception as exc:
            self.logger.error("Error checking for updates: %s", exc)
            raise

    def _parse_version_for_compare(self, version_str):
        """Parse release tags like 3.1.5-fix2 into a comparable version."""
        cleaned = (version_str or "").strip().lstrip("v")
        try:
            return version.parse(cleaned)
        except InvalidVersion:
            match = re.match(r"^(\d+\.\d+\.\d+)(?:[-_\.]?([A-Za-z]+)?(\d+)?)?$", cleaned)
            if match:
                base_version = match.group(1)
                suffix_number = match.group(3)
                if suffix_number:
                    return version.parse(f"{base_version}.post{suffix_number}")
                return version.parse(base_version)
            fallback = re.search(r"(\d+\.\d+\.\d+)", cleaned)
            if fallback:
                return version.parse(fallback.group(1))
            raise

    def _record_check(self):
        self.config["last_check"] = datetime.now().isoformat()
        self.save_update_config()

    def _fetch_releases(self):
        """Fetch release metadata from GitHub."""
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "LabelPrintServer-Updater",
        }

        if self.config.get("update_channel") == "stable":
            api_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            response = requests.get(api_url, headers=headers, timeout=20)
            response.raise_for_status()
            return [response.json()]

        api_url = f"https://api.github.com/repos/{self.github_repo}/releases"
        response = requests.get(api_url, headers=headers, timeout=20)
        response.raise_for_status()
        return response.json()

    def filter_releases_by_channel(self, releases):
        """Filter releases based on configured update channel."""
        channel = self.config.get("update_channel", "stable")
        if channel == "stable":
            return [release for release in releases if not release.get("prerelease")]
        if channel == "beta":
            return [release for release in releases if release.get("prerelease")]
        return releases

    def _select_release_asset(self, release):
        """Pick the installer asset the updater should download."""
        exe_assets = [asset for asset in release.get("assets", []) if asset["name"].lower().endswith(".exe")]
        if not exe_assets:
            return None

        preferred_name = self.config.get("asset_name_contains", "LabelPrintServer").lower()

        for asset in exe_assets:
            if preferred_name in asset["name"].lower():
                return asset

        for asset in exe_assets:
            if "setup" not in asset["name"].lower():
                return asset

        return exe_assets[0]

    def download_update(self, update_info, progress_callback=None):
        """Download the latest installer asset to a temp directory."""
        download_dir = Path(tempfile.gettempdir()) / "LabelPrintServerUpdate"
        download_dir.mkdir(parents=True, exist_ok=True)
        download_path = download_dir / update_info["asset_name"]

        self.logger.info("Downloading update asset from %s", update_info["download_url"])

        headers = {
            "Accept": "application/octet-stream",
            "User-Agent": "LabelPrintServer-Updater",
        }
        response = requests.get(update_info["download_url"], headers=headers, stream=True, timeout=60)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(download_path, "wb") as file_obj:
            for chunk in response.iter_content(chunk_size=1024 * 64):
                if not chunk:
                    continue
                file_obj.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    progress_callback(downloaded, total_size)

        if progress_callback:
            progress_callback(downloaded, total_size)

        self.logger.info("Downloaded update to %s", download_path)
        return download_path

    def install_update(self, download_path, update_info):
        """Stage the downloaded installer and launch it after shutdown."""
        updater_script = self._create_updater_script(Path(download_path), update_info["version"])
        self._launch_updater_script(updater_script)

        self.logger.info("Scheduled installer update to %s using %s", update_info["version"], download_path)
        return {
            "status": "scheduled",
            "version": update_info["version"],
            "installer_path": str(download_path),
            "message": (
                f"Update v{update_info['version']} downloaded. The installer will now run and "
                f"startup will stay enabled by default."
            ),
        }

    def _create_updater_script(self, installer_path, new_version):
        """Create a temporary batch script that launches the installer after shutdown."""
        updater_dir = Path(tempfile.gettempdir()) / "LabelPrintServerUpdate"
        updater_dir.mkdir(parents=True, exist_ok=True)
        script_path = updater_dir / f"apply_update_{int(time.time())}.bat"

        installer = str(installer_path)

        script_contents = f"""@echo off
setlocal
set "INSTALLER={installer}"
set "NEW_VERSION={new_version}"

timeout /t 2 /nobreak >nul

powershell -NoProfile -Command "Start-Process -FilePath '%INSTALLER%' -Verb RunAs -Wait -ArgumentList '/VERYSILENT /NORESTART /CLOSEAPPLICATIONS /TASKS=""startupicon""'"
del /Q "%INSTALLER%" >nul 2>&1
del /Q "%~f0" >nul 2>&1
"""

        script_path.write_text(script_contents, encoding="utf-8")
        return script_path

    def _launch_updater_script(self, script_path):
        """Launch the detached updater script."""
        creationflags = 0
        if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
            creationflags |= subprocess.CREATE_NEW_PROCESS_GROUP
        if hasattr(subprocess, "DETACHED_PROCESS"):
            creationflags |= subprocess.DETACHED_PROCESS

        subprocess.Popen(
            ["cmd.exe", "/c", str(script_path)],
            close_fds=True,
            creationflags=creationflags,
        )

    def check_and_update(self, force=False, auto_install=None):
        """Check GitHub and optionally download/stage the newer installer."""
        try:
            update_info = self.check_for_updates(force=force)
            if not update_info:
                return {"status": "no_update", "message": "No updates available"}

            should_auto_install = auto_install if auto_install is not None else self.config.get("auto_install", False)
            if should_auto_install:
                download_path = self.download_update(update_info)
                result = self.install_update(download_path, update_info)
                return result

            return {
                "status": "update_available",
                "version": update_info["version"],
                "release_name": update_info["release_name"],
                "asset_name": update_info["asset_name"],
                "published_at": update_info["published_at"],
                "changelog": update_info["changelog"],
                "html_url": update_info["html_url"],
                "message": f"Update {update_info['version']} is available",
            }
        except Exception as exc:
            self.logger.error("Error in check_and_update: %s", exc)
            return {"status": "error", "message": str(exc)}

    def manual_update(self, version_str=None):
        """Manually download and stage the latest update."""
        try:
            update_info = self.check_for_updates(force=True)
            if not update_info:
                return {"status": "no_update", "message": "No updates available"}

            if version_str and update_info["version"] != version_str:
                return {
                    "status": "error",
                    "message": f"Latest available version is {update_info['version']}, not {version_str}",
                }

            download_path = self.download_update(update_info)
            return self.install_update(download_path, update_info)
        except Exception as exc:
            self.logger.error("Manual update failed: %s", exc)
            return {"status": "error", "message": str(exc)}


class UpdateChecker:
    def __init__(self, update_manager, on_update_available=None):
        self.update_manager = update_manager
        self.on_update_available = on_update_available
        self.running = False
        self.thread = None

    def start(self):
        """Start background update checks."""
        if self.running or not self.update_manager.config.get("auto_check", True):
            return

        self.running = True
        self.thread = threading.Thread(target=self._check_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop background update checks."""
        self.running = False

    def _check_loop(self):
        """Periodically check for updates while respecting configured intervals."""
        while self.running:
            try:
                result = self.update_manager.check_and_update(force=False)
                if result.get("status") == "update_available" and self.on_update_available:
                    self.on_update_available(result)
            except Exception as exc:
                self.update_manager.logger.error("Background update check error: %s", exc)

            for _ in range(900):
                if not self.running:
                    return
                time.sleep(1)


def main():
    """Small CLI for manual update testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Label Print Server Update Manager")
    parser.add_argument("command", choices=["check", "update", "config", "status"])
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--auto-install", action="store_true")
    args = parser.parse_args()

    update_manager = UpdateManager()

    if args.command == "check":
        print(update_manager.check_and_update(force=args.force, auto_install=args.auto_install))
    elif args.command == "update":
        print(update_manager.manual_update())
    elif args.command == "config":
        print(json.dumps(update_manager.config, indent=2))
    elif args.command == "status":
        print(
            json.dumps(
                {
                    "current_version": update_manager.current_version,
                    "config": update_manager.config,
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
