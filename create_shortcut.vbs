Set WshShell = CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")
Set oUrlLink = WshShell.CreateShortcut(strDesktop & "\JARVIS.lnk")

' Link configuration pointing silently to VBScript runner
oUrlLink.TargetPath = "wscript.exe"
oUrlLink.Arguments = """C:\Users\Zezelabs2\.gemini\antigravity\scratch\zezelabs-brain\run_jarvis_silent.vbs"""
oUrlLink.WorkingDirectory = "C:\Users\Zezelabs2\.gemini\antigravity\scratch\zezelabs-brain"
oUrlLink.IconLocation = "C:\Users\Zezelabs2\.gemini\antigravity\scratch\zezelabs-brain\desktop\brain.ico"
oUrlLink.Description = "🏛️ ZEZELABS SİBER KARARGAH"
oUrlLink.Save()
