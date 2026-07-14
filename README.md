# VoiceDrop

VoiceDrop is a lightweight, fully local, offline speech-to-text dictation tool.

It records your voice, transcribes it with `whisper.cpp`, then optionally cleans filler words and self-corrections with `llama.cpp`.

The core dictation flow now works on Linux, macOS, and Windows.

- Linux: full GTK settings overlay + socket toggle daemon.
- macOS/Windows: headless dictation mode (no GTK UI) using the same local models.

All AI runs locally. No cloud APIs are required.

---

## What Makes Sense (And What Changed)

- Local-only AI: yes, already aligned with your goal.
- Fast and lightweight: yes, using native C++ engines and small models.
- Easy removal: now improved with per-OS uninstall scripts.
- Cross-platform: now organized with dedicated installers for Linux/macOS/Windows.

Important reality check:

- The GTK settings/overlay is Linux-specific.
- On macOS/Windows, VoiceDrop runs in headless mode when you call `--toggle`.

---

## Architecture

1. `whisper-server` on `127.0.0.1:8178` for speech-to-text.
2. `llama-server` on `127.0.0.1:8179` for cleanup/correction.
3. Runtime auto-starts local servers if they are not already running.
4. Linux keeps daemon + overlay behavior; other OSes use headless one-shot dictation.

---

## Installation (Simple Links)

Preferred path from the repo root:

```bash
python setup.py
```

That wizard detects your OS and runs the right installer for you. You can also pass `--prebuilt-dir /path/to/binaries` if you already have prebuilt `whisper-server` and `llama-server` binaries.

Linux:

```bash
curl -sSf https://raw.githubusercontent.com/ncisbani/VoiceDrop/main/install.sh | bash
```

macOS:

```bash
curl -sSf https://raw.githubusercontent.com/ncisbani/VoiceDrop/main/install-macos.sh | bash
```

Windows (PowerShell):

```powershell
iwr https://raw.githubusercontent.com/ncisbani/VoiceDrop/main/install-windows.ps1 -UseBasicParsing | iex
```

Uninstall links:

- Linux: `https://raw.githubusercontent.com/ncisbani/VoiceDrop/main/uninstall.sh`
- macOS: `https://raw.githubusercontent.com/ncisbani/VoiceDrop/main/uninstall-macos.sh`
- Windows: `https://raw.githubusercontent.com/ncisbani/VoiceDrop/main/uninstall-windows.ps1`

---

## Usage

Linux:

- Open settings UI: `python3 main.py`
- Toggle dictation: `python3 main.py --toggle`

macOS / Windows:

- Toggle dictation (headless): `python main.py --toggle`

Windows local test flow:

1. Run `python setup.py` and choose install.
2. Allow microphone and clipboard permissions if Windows prompts you.
3. Run `python main.py --toggle` and speak for a few seconds.
4. Toggle again or wait for silence detection to finish the cycle.

---

## Project Layout

- `installers/linux/*`: Linux install/uninstall.
- `installers/macos/*`: macOS install/uninstall.
- `installers/windows/*`: Windows install/uninstall.
- `install.sh`, `install-macos.sh`, `install-windows.ps1`: simple top-level launcher scripts.
- `uninstall.sh`, `uninstall-macos.sh`, `uninstall-windows.ps1`: simple top-level uninstall launchers.

---

## Notes

- Auto-paste may require accessibility/input permissions depending on OS.
- If no auto-paste backend is available, VoiceDrop still copies to clipboard.
- Model files are stored locally in `models/` and can be removed by uninstall scripts.

