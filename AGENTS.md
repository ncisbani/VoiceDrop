# AGENTS.md

## What

VoiceDrop. Offline voice dictation for Linux Wayland/GNOME. Records speech → whisper.cpp transcribes → llama.cpp cleans filler words → pastes at cursor.

## Run

```bash
# Open settings GUI
python3 main.py

# Toggle dictation (from CLI or GNOME shortcut)
python3 main.py --toggle
```

No tests. No CI. No linting. No type checking.

## Architecture

**Client-daemon over Unix socket** (`/tmp/voicedrop.sock`).
- First `--toggle`: spawns daemon (long-lived GTK process with socket server).
- Subsequent `--toggle`: sends toggle command to daemon via socket.
- Daemon dies after one record-transcribe-paste cycle.

**Two C++ engines** compiled as binaries in repo subdirs (gitignored):
- `whisper.cpp/build/bin/whisper-cli` — speech-to-text
- `llama.cpp/build/bin/llama-cli` — grammar/self-correction LLM

**GTK 3 overlay** (`overlay.py`): borderless transparent dot, bottom-center screen. Blue = listening, purple spinner = processing.

**Auto-paste** (`paster.py`): evdev uinput virtual device simulates Shift+Insert. Requires `input` group membership. Falls back to clipboard + notification.

## Config

`~/.config/voicedrop/config.json`. Keys: `language`, `whisper_model`, `llm_model`, `llm_correction`, `auto_paste`, `audio_device_index`.

Model paths in config auto-reset if missing or pointing to old models (migration logic in `config.py`).

## Models

In `models/` (gitignored). Downloaded by `download_models.py`:
- `ggml-tiny.bin` — whisper tiny model
- `smollm2-135m-instruct-q4_k_m.gguf` — SmolLM2 135M for grammar cleanup

## Setup Gotchas

- **uinput reboot required**: After install, must reboot/log out for `input` group to take effect. Auto-paste fails silently without it.
- **Distro-specific deps**: `install.sh` handles Debian/Fedora/Arch. Other distros need manual install of python3-pyaudio, python3-evdev, python3-numpy, python3-gi, cmake, wl-clipboard, libnotify.
- **Shortcut**: managed via GNOME gsettings custom-keybindings, not desktop file. Settings GUI handles registration.
- **No Python packaging**: no pyproject.toml, no requirements.txt. Dependencies are system packages.
