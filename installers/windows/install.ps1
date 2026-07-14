$ErrorActionPreference = 'Stop'

Write-Host "=== VoiceDrop Windows Installer ==="

$InstallDir = Join-Path $env:LOCALAPPDATA "VoiceDrop"
$BinDir = Join-Path $InstallDir "bin"
$PreferredBinDir = Join-Path $InstallDir "prebuilt\windows"
$ExternalPrebuiltDir = $env:VOICEDROP_PREBUILT_DIR

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git is required (install Git for Windows)."
}
if (-not (Get-Command cmake -ErrorAction SilentlyContinue)) {
    throw "cmake is required (install CMake)."
}
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "python is required (install Python 3)."
}

if (Test-Path (Join-Path $InstallDir ".git")) {
    Push-Location $InstallDir
    git pull
    Pop-Location
} else {
    git clone --depth 1 https://github.com/ncisbani/VoiceDrop.git $InstallDir
}

Push-Location $InstallDir

if (-not (Test-Path "whisper.cpp/.git")) {
    Remove-Item -Recurse -Force "whisper.cpp" -ErrorAction SilentlyContinue
    git clone --depth 1 https://github.com/ggerganov/whisper.cpp.git whisper.cpp
}
if (-not (Test-Path "llama.cpp/.git")) {
    Remove-Item -Recurse -Force "llama.cpp" -ErrorAction SilentlyContinue
    git clone --depth 1 https://github.com/ggerganov/llama.cpp.git llama.cpp
}

python -m pip install --user --upgrade pip
python -m pip install --user pyaudio numpy

if ($ExternalPrebuiltDir) {
    $PreferredBinDir = $ExternalPrebuiltDir
}

if ((Test-Path (Join-Path $PreferredBinDir "whisper-server.exe")) -and (Test-Path (Join-Path $PreferredBinDir "llama-server.exe"))) {
    Write-Host "Using prebuilt binaries from $PreferredBinDir"
    New-Item -ItemType Directory -Force -Path "whisper.cpp\build\bin" | Out-Null
    New-Item -ItemType Directory -Force -Path "llama.cpp\build\bin" | Out-Null
    Copy-Item (Join-Path $PreferredBinDir "whisper-server.exe") "whisper.cpp\build\bin\"
    Copy-Item (Join-Path $PreferredBinDir "llama-server.exe") "llama.cpp\build\bin\"
} else {
    cmake -S whisper.cpp -B whisper.cpp/build -DWHISPER_BUILD_TESTS=OFF -DWHISPER_BUILD_EXAMPLES=ON
    cmake --build whisper.cpp/build --config Release --target whisper-server

    cmake -S llama.cpp -B llama.cpp/build -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=ON
    cmake --build llama.cpp/build --config Release --target llama-server
}

python download_models.py

New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
$ToggleCmd = Join-Path $BinDir "voicedrop-toggle.cmd"
"@echo off`r`npython `"$InstallDir\main.py`" --toggle`r`n" | Set-Content -Path $ToggleCmd -Encoding ASCII

Write-Host "Install complete."
Write-Host "Run dictation with: $ToggleCmd"
Write-Host "If auto-paste fails, allow accessibility/automation permissions for your terminal."

Pop-Location
