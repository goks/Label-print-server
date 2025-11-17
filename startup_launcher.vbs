Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get the script directory
scriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Paths
pythonw = scriptDir & "\.venv\Scripts\pythonw.exe"
appScript = scriptDir & "\tray_app_v2.py"

' Check if files exist
If Not objFSO.FileExists(pythonw) Then
    WScript.Quit
End If

If Not objFSO.FileExists(appScript) Then
    WScript.Quit
End If

' Launch the application silently
objShell.Run """" & pythonw & """ """ & appScript & """", 0, False

Set objShell = Nothing
Set objFSO = Nothing
