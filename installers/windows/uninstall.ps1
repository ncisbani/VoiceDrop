$ErrorActionPreference = 'Stop'

Write-Host "=== VoiceDrop Windows Uninstaller ==="
$InstallDir = Join-Path $env:LOCALAPPDATA "VoiceDrop"
$ConfigDir = Join-Path $env:APPDATA "VoiceDrop"

$confirm = Read-Host "Remove VoiceDrop and local models? (y/N)"
if ($confirm -notmatch '^[Yy]$') {
    Write-Host "Aborted."
    exit 0
}

Get-Process whisper-server -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

if (Test-Path $InstallDir) {
    Remove-Item -Recurse -Force $InstallDir
}
if (Test-Path $ConfigDir) {
    Remove-Item -Recurse -Force $ConfigDir
}

Write-Host "VoiceDrop removed."
