Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' 1. Delete old confusing shortcut if exists
oldShortcut = "C:\Users\Zezelabs2\Desktop\JARVIS.lnk"
If fso.FileExists(oldShortcut) Then
    fso.DeleteFile(oldShortcut)
End If

' 2. Create brand new premium ZEZELABS HQ shortcut
Set oUrlLink = WshShell.CreateShortcut("C:\Users\Zezelabs2\Desktop\ZEZE-HQ JARVIS.lnk")

oUrlLink.TargetPath = "wscript.exe"
oUrlLink.Arguments = """C:\Users\Zezelabs2\.gemini\antigravity\scratch\zezelabs-brain\run_jarvis_silent.vbs"""
oUrlLink.WorkingDirectory = "C:\Users\Zezelabs2\.gemini\antigravity\scratch\zezelabs-brain"
oUrlLink.IconLocation = "C:\Users\Zezelabs2\.gemini\antigravity\scratch\zezelabs-brain\desktop\brain.ico"
oUrlLink.Description = "🏛️ ZEZELABS SİBER KARARGAH"
oUrlLink.Save()
