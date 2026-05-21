# Start Jarvis Desktop UI
# Run this from terminal or double click it

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location -Path $RepoRoot

$env:ZOM_ENABLE_AUTO_GITHUB_PUSH="false"
$env:ZOM_ENABLE_VOICE_LISTENER="false"

pythonw desktop/jarvis_desktop.py
if ($LASTEXITCODE -ne 0) {
    python desktop/jarvis_desktop.py
}
