Set WshShell = CreateObject("WScript.Shell")
' Absolute path pointing directly to active user desktop
Set oUrlLink = WshShell.CreateShortcut("C:\Users\Zezelabs2\Desktop\JARVIS.lnk")

oUrlLink.TargetPath = "wscript.exe"
oUrlLink.Arguments = """C:\Users\Zezelabs2\.gemini\antigravity\scratch\zezelabs-brain\run_jarvis_silent.vbs"""
oUrlLink.WorkingDirectory = "C:\Users\Zezelabs2\.gemini\antigravity\scratch\zezelabs-brain"
oUrlLink.IconLocation = "C:\Users\Zezelabs2\.gemini\antigravity\scratch\zezelabs-brain\desktop\brain.ico"
oUrlLink.Description = "🏛️ ZEZELABS SİBER KARARGAH"
oUrlLink.Save()
