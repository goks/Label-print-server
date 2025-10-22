Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
batFile = scriptDir & "\run_tray.bat"

' Run the batch file hidden (no console window)
WshShell.Run """" & batFile & """", 0, False

' Clean up
Set WshShell = Nothing
Set fso = Nothing