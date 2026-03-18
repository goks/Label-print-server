; Label Print Server - NSIS Installer Script
; This creates a standalone installer that bundles Python and all dependencies

!define APP_NAME "Label Print Server"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "Label Print Server"
!define APP_EXE "tray_app_v2.py"
!define INSTALL_DIR "$PROGRAMFILES\LabelPrintServer"

; Modern UI
!include "MUI2.nsh"
!include "FileFunc.nsh"

; Installer settings
Name "${APP_NAME}"
OutFile "LabelPrintServer_Setup.exe"
InstallDir "${INSTALL_DIR}"
InstallDirRegKey HKLM "Software\${APP_NAME}" "InstallDir"
RequestExecutionLevel admin

; Modern UI Configuration
!define MUI_ABORTWARNING
!define MUI_ICON "icons\app_icon.ico"
!define MUI_UNICON "icons\app_icon.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "icons\app_icon.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "icons\app_icon.ico"
!define MUI_WELCOMEPAGE_TITLE "Welcome to ${APP_NAME} Setup"
!define MUI_WELCOMEPAGE_TEXT "This wizard will guide you through the installation of ${APP_NAME}.$\r$\n$\r$\nThis application allows you to print labels using BarTender templates from any device on your network.$\r$\n$\r$\nClick Next to continue."
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_TEXT "Start ${APP_NAME} now"
!define MUI_FINISHPAGE_RUN_FUNCTION "LaunchApplication"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "README.md"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"

; Version Information
VIProductVersion "1.0.0.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "CompanyName" "${APP_PUBLISHER}"
VIAddVersionKey "FileDescription" "${APP_NAME} Installer"
VIAddVersionKey "FileVersion" "${APP_VERSION}"

; Installer Section
Section "Install"
    
    ; Check if application is running and kill it
    DetailPrint "Checking for running instances..."
    nsExec::ExecToStack 'taskkill /F /IM pythonw.exe'
    Pop $0 ; Return value
    Sleep 2000
    
    ; Remove previous installation if exists
    DetailPrint "Removing previous installation..."
    
    ; Remove old startup entries (both registry and VBS)
    DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "LabelPrintServer"
    Delete "$INSTDIR\startup_launcher.vbs"
    
    ; Remove old shortcuts
    Delete "$DESKTOP\Label Print Server.lnk"
    Delete "$DESKTOP\${APP_NAME}.lnk"
    RMDir /r "$SMPROGRAMS\${APP_NAME}"
    
    ; Clean old installation directory
    RMDir /r "$INSTDIR\templates"
    RMDir /r "$INSTDIR\icons"
    RMDir /r "$INSTDIR\.venv"
    RMDir /r "$INSTDIR\logs"
    Delete "$INSTDIR\*.py"
    Delete "$INSTDIR\*.md"
    Delete "$INSTDIR\*.json"
    Delete "$INSTDIR\*.txt"
    Delete "$INSTDIR\*.vbs"
    Delete "$INSTDIR\*.bat"
    Delete "$INSTDIR\Uninstall.exe"
    
    SetOutPath "$INSTDIR"
    
    ; Show installation progress
    DetailPrint "Installing ${APP_NAME}..."
    
    ; Copy all files
    File "app.py"
    File "tray_app_v2.py"
    File "printed_db.py"
    File "update_manager.py"
    File "wsgi.py"
    File "requirements.txt"
    File "VERSION"
    File "README.md"
    File "FUNCTIONS.md"
    File "update_config.json"
    File "db_settings.json"
    File "startup_launcher.vbs"
    File "run_tray.bat"
    File "debug_launcher.bat"
    File "fix_python_paths.bat"
    
    ; Copy directories
    File /r "templates"
    File /r "icons"
    File /r "python_standalone"
    
    ; Rename to python for cleaner paths
    DetailPrint "Setting up Python runtime..."
    Rename "$INSTDIR\python_standalone" "$INSTDIR\python"
    
    ; Create logs directory
    CreateDirectory "$INSTDIR\logs"
    
    ; Create AppData directory for settings
    SetShellVarContext current
    CreateDirectory "$LOCALAPPDATA\LabelPrintServer"
    CreateDirectory "$LOCALAPPDATA\LabelPrintServer\logs"
    CreateDirectory "$LOCALAPPDATA\LabelPrintServer\data"
    
    ; Store installation folder
    WriteRegStr HKLM "Software\${APP_NAME}" "InstallDir" "$INSTDIR"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
    ; Add to Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayIcon" "$INSTDIR\icons\app_icon.ico"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "HelpLink" "http://localhost:5000"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoRepair" 1
    
    ; Get installation size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "EstimatedSize" "$0"
    
    ; Create desktop shortcut with icon using BAT launcher
    SetOutPath "$INSTDIR"
    CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\run_tray.bat" "" "$INSTDIR\icons\app_icon.ico"
    
    ; Create Start Menu shortcuts with icons
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\run_tray.bat" "" "$INSTDIR\icons\app_icon.ico"
    
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" \
        "$INSTDIR\Uninstall.exe" \
        "" \
        "$INSTDIR\icons\app_icon.ico" \
        0
    
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\Open Web Interface.lnk" \
        "http://localhost:5000" \
        "" \
        "$INSTDIR\icons\app_icon.ico" \
        0
    
    ; Note: Auto-start is now controlled by the tray app itself
    ; Users can enable/disable via tray menu
    
    DetailPrint "Installation completed successfully!"
    
SectionEnd

; Launch function
Function LaunchApplication
    SetOutPath "$INSTDIR"
    Exec '"$INSTDIR\run_tray.bat"'
FunctionEnd

; Uninstaller Section
Section "Uninstall"
    
    ; Kill the application if running
    DetailPrint "Stopping ${APP_NAME}..."
    nsExec::ExecToStack 'taskkill /F /IM pythonw.exe'
    Pop $0
    nsExec::ExecToStack 'taskkill /F /IM python.exe'
    Pop $0
    Sleep 2000
    
    ; Remove from startup (all possible entries)
    DetailPrint "Removing startup entries..."
    DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "LabelPrintServer"
    DeleteRegValue HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "LabelPrintServer"
    Delete "$INSTDIR\startup_launcher.vbs"
    
    ; Remove files
    DetailPrint "Removing files..."
    Delete "$INSTDIR\app.py"
    Delete "$INSTDIR\tray_app.py"
    Delete "$INSTDIR\tray_app_v2.py"
    Delete "$INSTDIR\tray_gui.py"
    Delete "$INSTDIR\printed_db.py"
    Delete "$INSTDIR\update_manager.py"
    Delete "$INSTDIR\wsgi.py"
    Delete "$INSTDIR\requirements.txt"
    Delete "$INSTDIR\VERSION"
    Delete "$INSTDIR\README.md"
    Delete "$INSTDIR\FUNCTIONS.md"
    Delete "$INSTDIR\update_config.json"
    Delete "$INSTDIR\db_settings.json"
    Delete "$INSTDIR\startup_launcher.vbs"
    Delete "$INSTDIR\Uninstall.exe"
    Delete "$INSTDIR\*.bat"
    Delete "$INSTDIR\*.log"
    
    ; Remove directories
    DetailPrint "Removing directories..."
    RMDir /r "$INSTDIR\templates"
    RMDir /r "$INSTDIR\icons"
    RMDir /r "$INSTDIR\.venv"
    RMDir /r "$INSTDIR\logs"
    RMDir /r "$INSTDIR\build"
    RMDir /r "$INSTDIR\__pycache__"
    
    ; Remove shortcuts
    DetailPrint "Removing shortcuts..."
    Delete "$DESKTOP\${APP_NAME}.lnk"
    Delete "$DESKTOP\Label Print Server.lnk"
    RMDir /r "$SMPROGRAMS\${APP_NAME}"
    
    ; Remove installation directory
    RMDir "$INSTDIR"
    
    ; Remove registry keys
    DetailPrint "Removing registry entries..."
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
    DeleteRegKey HKLM "Software\${APP_NAME}"
    
    ; Ask if user wants to remove settings
    MessageBox MB_YESNO|MB_ICONQUESTION "Do you want to remove all settings and data?$\r$\n$\r$\nThis includes database configuration, logs, and print history." IDNO SkipDataRemoval
        SetShellVarContext current
        DetailPrint "Removing user data..."
        RMDir /r "$LOCALAPPDATA\LabelPrintServer"
    SkipDataRemoval:
    
    DetailPrint "Uninstallation completed successfully!"
    
SectionEnd
