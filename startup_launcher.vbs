Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get the script directory
scriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Paths for embedded Python
pythonw = scriptDir & "\python\pythonw.exe"
appScript = scriptDir & "\tray_app_v2.py"

' Check if files exist
If Not objFSO.FileExists(pythonw) Then
    MsgBox "Python runtime not found at:" & vbCrLf & pythonw & vbCrLf & vbCrLf & _
           "Please reinstall the application.", vbCritical, "Label Print Server Error"
    WScript.Quit
End If

If Not objFSO.FileExists(appScript) Then
    MsgBox "Application script not found at:" & vbCrLf & appScript & vbCrLf & vbCrLf & _
           "Please reinstall the application.", vbCritical, "Label Print Server Error"
    WScript.Quit
End If

' Set working directory and launch the application silently
objShell.CurrentDirectory = scriptDir
objShell.Run """" & pythonw & """ """ & appScript & """", 0, False

Set objShell = Nothing
Set objFSO = Nothing
