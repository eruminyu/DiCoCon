Set WshShell = CreateObject("WScript.Shell")
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strPath
WshShell.Run Chr(34) & strPath & "\.venv\Scripts\pythonw.exe" & Chr(34) & " " & Chr(34) & strPath & "\bot.py" & Chr(34), 0, False
MsgBox "디스코드 콘 봇이 백그라운드에서 실행되었습니다!" & vbCrLf & "(종료하려면 '백그라운드_종료.bat'을 실행하세요)", vbInformation, "Discord ConBot"
