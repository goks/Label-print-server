; Inno Setup Script for Label Print Server
; Features:
; - Removes previous installations before installing
; - Checks for and kills running instances
; - Optional startup with Windows
; - Preserves data files (db_settings.json, logs) on uninstall

#define MyAppName "Label Print Server"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Your Company"
#define MyAppExeName "LabelPrintServer.exe"

[Setup]
AppId={{8F9C7E6D-4A3B-4F2E-9D1C-5E8A7B6C4D3E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\LabelPrintServer
DefaultGroupName={#MyAppName}
OutputBaseFilename=LabelPrintServer_Setup
Compression=lzma2/ultra64
SolidCompression=yes
OutputDir=Output
PrivilegesRequired=admin
SetupIconFile=icons\app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
VersionInfoVersion={#MyAppVersion}
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupicon"; Description: "Start with Windows"; GroupDescription: "Additional options:"

[Files]
Source: "dist\LabelPrintServer.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "templates\*"; DestDir: "{app}\templates"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "icons\*"; DestDir: "{app}\icons"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "LabelPrintServer"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall

[UninstallDelete]
Type: filesandordirs; Name: "{app}\build"
Type: filesandordirs; Name: "{app}\dist"
Type: filesandordirs; Name: "{app}\__pycache__"
Type: files; Name: "{app}\*.pyc"
Type: files; Name: "{app}\*.pyo"
Type: files; Name: "{app}\*.spec"
Type: files; Name: "{app}\*.bat"
Type: files; Name: "{app}\{#MyAppExeName}"

[Code]
// Function to kill running instances of the application
function KillRunningInstances(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  // Kill any running instances
  Exec('taskkill', '/F /IM LabelPrintServer.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Exec('taskkill', '/F /IM python.exe /FI "WINDOWTITLE eq Label Print Server*"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Exec('taskkill', '/F /IM pythonw.exe /FI "WINDOWTITLE eq Label Print Server*"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Sleep(2000); // Wait for processes to terminate
end;

// Function to remove old startup entries
function RemoveStartupEntries(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  // Remove registry startup entries
  RegDeleteValue(HKEY_CURRENT_USER, 'Software\Microsoft\Windows\CurrentVersion\Run', 'LabelPrintServer');
  RegDeleteValue(HKEY_LOCAL_MACHINE, 'Software\Microsoft\Windows\CurrentVersion\Run', 'LabelPrintServer');
  
  // Remove startup shortcuts if they exist
  DeleteFile(ExpandConstant('{userstartup}\Label Print Server.lnk'));
  DeleteFile(ExpandConstant('{commonstartup}\Label Print Server.lnk'));
end;

// Function to check if this is a reinstall/upgrade
function IsUpgrade(): Boolean;
var
  sPrevPath: String;
begin
  sPrevPath := '';
  if RegQueryStringValue(HKEY_LOCAL_MACHINE,
    'Software\Microsoft\Windows\CurrentVersion\Uninstall\{8F9C7E6D-4A3B-4F2E-9D1C-5E8A7B6C4D3E}_is1',
    'Inno Setup: App Path', sPrevPath) then
    Result := True
  else if RegQueryStringValue(HKEY_CURRENT_USER,
    'Software\Microsoft\Windows\CurrentVersion\Uninstall\{8F9C7E6D-4A3B-4F2E-9D1C-5E8A7B6C4D3E}_is1',
    'Inno Setup: App Path', sPrevPath) then
    Result := True
  else
    Result := False;
end;

// Pre-installation cleanup
function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  NeedsRestart := False;
  
  if IsUpgrade() then
  begin
    Log('Upgrade detected. Performing cleanup...');
    if not KillRunningInstances() then
    begin
      Result := 'Failed to stop running instances. Please close the application manually and try again.';
      Exit;
    end;
    RemoveStartupEntries();
  end;
end;

// Before installation starts
function InitializeSetup(): Boolean;
begin
  Result := True;
  
  // Kill any running instances before setup
  if IsUpgrade() then
  begin
    if MsgBox('A previous installation was detected. Setup will close any running instances and remove old startup entries before installing. Continue?', 
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      KillRunningInstances();
      RemoveStartupEntries();
      Result := True;
    end
    else
      Result := False;
  end;
end;

// Before uninstall starts
function InitializeUninstall(): Boolean;
begin
  Result := True;
  if MsgBox('Do you want to completely remove Label Print Server? Note: Your database settings and log files will be preserved.', 
            mbConfirmation, MB_YESNO) = IDYES then
  begin
    KillRunningInstances();
    RemoveStartupEntries();
    Result := True;
  end
  else
    Result := False;
end;

// Custom uninstall to preserve data files
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Keep data files - they are not listed in [Files] section
    // db_settings.json and logs folder will remain
    Log('Uninstall complete. Data files preserved.');
  end;
end;
