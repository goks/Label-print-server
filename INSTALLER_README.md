# Label Print Server - Installer Documentation

## Overview
This installer provides a complete, professional installation experience for the Label Print Server application with advanced features for upgrade handling and data preservation.

## Installer Features

### 1. **Clean Reinstallation**
- Automatically detects previous installations
- Removes all old program files before installing new version
- Prompts user for confirmation before upgrade
- Ensures no conflicts between versions

### 2. **Process Management**
- Checks for running instances of Label Print Server
- Automatically terminates all running processes before installation
- Waits for processes to close gracefully
- Prevents file-in-use errors during installation

### 3. **Startup Configuration**
- Optional "Start with Windows" checkbox during installation
- Adds application to Windows Registry startup entries (HKCU)
- No manual configuration required
- Easy to enable/disable during installation

### 4. **Smart Uninstallation**
- Preserves critical data files:
  - `db_settings.json` - Database configuration
  - `logs\` folder - All log files
  - Any user-created data files
- Removes only program files and executables
- Cleans up all startup entries
- Terminates running processes before uninstall

## Building the Installer

### Prerequisites
1. **Python 3.9+** with virtual environment
2. **PyInstaller** installed in virtual environment
3. **Inno Setup 6** - Download from: https://jrsoftware.org/isdl.php

### Build Steps

#### Option 1: Automated Build (Recommended)
```batch
build_full_installer.bat
```

This script will:
1. Build the PyInstaller executable from source
2. Check for Inno Setup installation
3. Compile the complete installer
4. Output to `Output\LabelPrintServer_Setup.exe`

#### Option 2: Manual Build
```batch
# Step 1: Build executable
.venv\Scripts\pyinstaller.exe --clean --noconfirm LabelPrintServer.spec

# Step 2: Compile installer (requires Inno Setup)
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

## Installation Process

### First-Time Installation
1. Run `LabelPrintServer_Setup.exe`
2. Choose installation directory (default: `C:\Program Files\LabelPrintServer`)
3. Select optional tasks:
   - Create desktop icon
   - Start with Windows
4. Click Install
5. Optionally launch application after installation

### Upgrading from Previous Version
1. Run `LabelPrintServer_Setup.exe`
2. Installer detects previous version
3. Confirms upgrade with user
4. Automatically:
   - Stops running instances
   - Removes old startup entries
   - Cleans up old program files
   - Preserves data files
5. Installs new version
6. Restores startup configuration if selected

### Uninstallation
1. Use Windows "Add or Remove Programs"
2. Or run uninstaller from Start Menu: "Uninstall Label Print Server"
3. Confirms uninstallation
4. Automatically:
   - Stops running application
   - Removes startup entries
   - Deletes program files
   - **Preserves** `db_settings.json` and `logs\` folder
5. Data files remain in installation directory for future reinstallation

## File Structure After Installation

```
C:\Program Files\LabelPrintServer\
├── LabelPrintServer.exe          # Main application (removed on uninstall)
├── templates\                     # HTML templates (removed on uninstall)
├── icons\                         # Application icons (removed on uninstall)
├── README.md                      # Documentation (removed on uninstall)
├── db_settings.json              # Database config (PRESERVED on uninstall)
└── logs\                         # Log files (PRESERVED on uninstall)
    ├── access.log.*
    ├── database.log.*
    └── label_print_server.log.*
```

## Registry Entries

### Startup Entry (if enabled)
```
HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run
Name: LabelPrintServer
Value: "C:\Program Files\LabelPrintServer\LabelPrintServer.exe"
```

### Uninstall Entry
```
HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Uninstall\{8F9C7E6D-4A3B-4F2E-9D1C-5E8A7B6C4D3E}_is1
```

## Troubleshooting

### Installer Won't Run
- Ensure you have Administrator privileges
- Check Windows SmartScreen hasn't blocked the installer
- Right-click installer → Properties → Unblock

### Application Won't Start After Install
- Check Windows Firewall settings
- Verify SQL Server is accessible
- Review logs in `C:\Program Files\LabelPrintServer\logs\`

### Upgrade Issues
- Manually close application before upgrade if prompted
- Check Task Manager for hung processes
- Restart computer if processes won't terminate

### Uninstall Leaves Files
- This is intentional - data files are preserved
- To completely remove:
  - Manually delete `C:\Program Files\LabelPrintServer\` folder after uninstall
  - Or keep for future reinstallation (preserves settings)

## Advanced Configuration

### Silent Installation
```batch
LabelPrintServer_Setup.exe /SILENT
```

### Silent Installation with Startup
```batch
LabelPrintServer_Setup.exe /SILENT /TASKS="startupicon"
```

### Silent Uninstall
```batch
"C:\Program Files\LabelPrintServer\unins000.exe" /SILENT
```

### Custom Installation Directory
```batch
LabelPrintServer_Setup.exe /DIR="D:\MyApps\LabelPrintServer"
```

## Security Considerations

- Installer requires Administrator privileges
- Application runs with user privileges
- Database connection uses Windows Authentication
- No passwords stored in executable
- Settings stored in plain JSON (file system security applies)

## Support

For issues or questions:
1. Check log files in `logs\` folder
2. Review database connectivity in settings
3. Ensure SQL Server is accessible
4. Verify printer is set as default in Windows

## Version History

### Version 1.0.0
- Initial installer release
- PyInstaller-based single executable
- Inno Setup installer with upgrade support
- Data preservation on uninstall
- Startup configuration option
- Process management and cleanup
