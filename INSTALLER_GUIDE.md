# Label Print Server - NSIS Installer Guide

## Overview
This project uses **NSIS (Nullsoft Scriptable Install System)** to create a professional standalone installer that bundles Python and all dependencies. No Python installation required on target machines!

## Prerequisites

### Installing NSIS
1. Download NSIS from: https://nsis.sourceforge.io/Download
2. Run the installer (recommended: install to default location `C:\Program Files (x86)\NSIS`)
3. NSIS is automatically added to PATH during installation
4. Verify installation by opening CMD and typing: `makensis /VERSION`

## Building the Installer

### Quick Start
1. Open PowerShell or CMD in the project directory
2. Run: `build_installer.bat`
3. Output: `LabelPrintServer_Setup.exe` (~32 MB)

### What the Build Script Does:
- ✅ Checks for NSIS installation
- ✅ Verifies virtual environment exists
- ✅ Builds installer using `installer.nsi`
- ✅ Creates `LabelPrintServer_Setup.exe`

## Installer Features

### Installation Process:
1. **Removes old installations automatically**
   - Kills running application processes
   - Removes old startup registry entries
   - Cleans up old shortcuts
   - Removes previous installation files
   
2. **Fresh Installation**
   - Installs to `C:\Program Files\LabelPrintServer`
   - Creates desktop shortcut with icon
   - Creates Start Menu shortcuts with icons
   - Sets up AppData directories for logs/data
   - Registers in Add/Remove Programs

3. **Icons Used Everywhere**
   - Desktop shortcut icon
   - Start Menu shortcut icons
   - Uninstaller icon
   - Add/Remove Programs icon
   - Web interface shortcut icon

### Uninstallation Process:
1. **Stops Application**
   - Terminates all pythonw.exe processes
   - Waits for clean shutdown

2. **Removes Startup Entries**
   - Deletes HKCU startup registry entries
   - Deletes HKLM startup registry entries
   - Removes startup_launcher.vbs

3. **Cleans Installation**
   - Removes all program files
   - Removes all shortcuts
   - Removes registry entries
   - Optionally removes user data

## What Gets Bundled

The installer includes:
- ✅ **Python virtual environment** (`.venv/`) - Fully self-contained
- ✅ **All Python packages** from requirements.txt
- ✅ **Application files** (app.py, tray_app_v2.py, etc.)
- ✅ **Templates** (HTML templates)
- ✅ **Icons** (application icons for shortcuts and UI)
- ✅ **Configuration files** (db_settings.json, etc.)

## Distribution

### Single File Distribution:
**File:** `LabelPrintServer_Setup.exe` (~32 MB)

You can:
- Copy to USB drive
- Share via network
- Email (if size permits)
- Upload to file server

**No additional files needed!** The installer is completely standalone.

## Installing on Target PC

On the target PC (no Python required):
1. Double-click `LabelPrintServer_Setup.exe`
2. Click "Next" through the wizard
3. Choose installation directory (or use default)
4. Click "Install"
5. Check "Start Label Print Server now" on finish screen
6. Done! App runs from system tray with proper icon

### What Target PC Needs:
- Windows 10 or later
- **No Python required**
- **No NSIS required**
- SQL Server access (configured after installation)
- BarTender (for label printing)

## Uninstalling

### Via Add/Remove Programs:
1. Open Settings → Apps → Apps & features
2. Search for "Label Print Server"
3. Click Uninstall
4. Choose whether to keep settings and data

### Via Start Menu:
1. Start → Label Print Server → Uninstall
2. Follow prompts

### What Gets Removed:
- ✅ All program files from Program Files
- ✅ Desktop shortcut
- ✅ Start Menu shortcuts
- ✅ Startup registry entries (all variants)
- ✅ Add/Remove Programs entry
- ✅ Optionally: User data and logs

## Installer Improvements

### New in This Version:
1. **Automatic Cleanup**
   - Removes old installations before installing
   - No manual uninstall needed for upgrades

2. **Complete Startup Removal**
   - Removes HKCU registry entries
   - Removes HKLM registry entries
   - Deletes VBS launcher files

3. **Enhanced Icons**
   - Icons on all shortcuts
   - Icon in Add/Remove Programs
   - Icon in installer UI

4. **Better Process Management**
   - Properly terminates running app
   - Waits for clean shutdown
   - Handles both pythonw.exe and python.exe

## Customization

### Changing App Icon:
Edit `installer.nsi`:
```nsis
!define MUI_ICON "icons\your_icon.ico"
!define MUI_UNICON "icons\your_icon.ico"
```

### Changing Version:
Edit `installer.nsi`:
```nsis
!define APP_VERSION "1.0.1"
VIProductVersion "1.0.1.0"
```

### Adding Files:
Edit the `Section "Install"` in `installer.nsi`:
```nsis
File "your_new_file.py"
```

## Troubleshooting

### "NSIS not found" error:
- Install NSIS from https://nsis.sourceforge.io/Download
- It should auto-add to PATH during installation
- If not, add manually: `C:\Program Files (x86)\NSIS`

### "Virtual environment not found":
- Make sure `.venv` folder exists
- Run: `python -m venv .venv`
- Install dependencies: `.venv\Scripts\pip install -r requirements.txt`

### Installer is large (~32 MB):
- This is normal - includes Python runtime + dependencies
- Cannot be significantly reduced
- Python environment must be bundled

### Installation fails on target PC:
- Run installer as Administrator
- Check antivirus isn't blocking
- Ensure enough disk space (~100 MB)

### "Python not found" error on target PC:
- The `.venv` folder should be copied with correct structure
- Verify `C:\Program Files\LabelPrintServer\.venv\Scripts\pythonw.exe` exists
- If missing, the installer didn't complete - try reinstalling
- Check installer log: `%TEMP%\nsis_install.log`

### Application doesn't start after installation:
- Try running manually: Double-click the desktop shortcut
- If error appears, note the exact Python path in the error message
- The VBS launcher will show error dialog if Python is not found
- Reinstall using the latest installer version

### Old shortcuts remain after reinstall:
- Installer now removes them automatically
- If persistent, delete manually from Desktop and Start Menu

## Version Updates

To create a new version:
1. Update `VERSION` file
2. Edit `installer.nsi` and change:
   ```nsis
   !define APP_VERSION "1.0.1"
   VIProductVersion "1.0.1.0"
   ```
3. Rebuild: `build_installer.bat`
4. New installer reflects updated version

## Technical Details

### Build Method:
- **Tool:** NSIS (Nullsoft Scriptable Install System)
- **Output:** Single .exe installer
- **Compression:** zlib (41.5% compression ratio)
- **Size:** ~32 MB

### Installation Locations:
- **Program:** `C:\Program Files\LabelPrintServer\`
- **Data:** `%LOCALAPPDATA%\LabelPrintServer\`
- **Logs:** `%LOCALAPPDATA%\LabelPrintServer\logs\`
- **Settings:** `%LOCALAPPDATA%\LabelPrintServer\data\`

### Registry Keys:
- **Install Info:** `HKLM\Software\Label Print Server`
- **Uninstall:** `HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\Label Print Server`
- **Startup (optional):** `HKCU\Software\Microsoft\Windows\CurrentVersion\Run\LabelPrintServer`

## Best Practices

1. **Always test installer** on a clean VM before distribution
2. **Increment version number** for each release
3. **Document changes** in VERSION file or changelog
4. **Keep installer.nsi** under version control
5. **Sign the installer** for production (optional but recommended)

## Production Checklist

Before distributing:
- [ ] Updated VERSION file
- [ ] Updated version in installer.nsi
- [ ] Tested installation on clean PC
- [ ] Tested uninstallation completely removes everything
- [ ] Tested upgrade (old version → new version)
- [ ] Verified all icons display correctly
- [ ] Verified startup entries are handled correctly
- [ ] Tested on Windows 10 and Windows 11

---

**Ready to distribute!** The installer handles everything automatically - no Python needed on target PCs!
