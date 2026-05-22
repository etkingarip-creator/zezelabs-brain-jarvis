$target = "C:\Python314\python.exe"
$script = "C:\Users\Zezelabs2\.gemini\antigravity\scratch\zezelabs-brain\desktop\jarvis_desktop.py"
$workdir = "C:\Users\Zezelabs2\.gemini\antigravity\scratch\zezelabs-brain"
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcut = "$desktop\JARVIS.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$short = $WshShell.CreateShortcut($shortcut)
$short.TargetPath = $target
$short.Arguments = $script
$short.WorkingDirectory = $workdir
$short.Description = "🏛️ ZEZE-LABS JARVIS"
$short.IconLocation = "C:\Users\Zezelabs2\.gemini\antigravity\scratch\zezelabs-brain\desktop\brain.ico"
$short.Save()

Write-Host "✅ JARVIS kısayolu -> $shortcut"
