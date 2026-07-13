# VoiceDrop

VoiceDrop is an ultra-lightweight, 100% offline, local voice dictation application designed for Linux (Wayland/GNOME). It captures your voice, transcribes it locally using `whisper.cpp`, cleans up filler words and self-corrections using `llama.cpp` with a tiny 0.5B LLM, and pastes the result directly at your active text cursor.

When triggered, it displays a minimal glassmorphic visualizer at the bottom center of your screen, letting you know it's listening. Click it or press your shortcut again to stop, process, and paste.

---

## Architecture & Design

1. **Light & Fast C++ Engines**: Runs `whisper.cpp` (speech-to-text) and `llama.cpp` (grammar/self-correction LLM) compiled natively. They start instantly and consume very little RAM compared to Python PyTorch/Transformers.
2. **Native GNOME Integration**: Built using PyGObject (GTK 3) and styled with CSS. The transparent, borderless overlay window runs natively on Wayland.
3. **Uinput Auto-Paste**: Bypasses Wayland security barriers using Linux `evdev` to create a virtual input device, typing `Ctrl+V` automatically wherever your cursor is.
4. **Client-Daemon Pattern**: A single UNIX Domain Socket `/tmp/voicedrop.sock` manages recording toggle. Calling `main.py --toggle` starts recording if idle, or stops & transcribes if recording.

---

## Setup & Installation

To install VoiceDrop automatically (clones the app, compiles engines, downloads lightweight models, configures permissions, registers the launcher, and binds a default shortcut):

Run this one-liner in your terminal:

```bash
curl -sSf https://raw.githubusercontent.com/ncisbani/VoiceDrop/main/install.sh | bash
```

> [!IMPORTANT]
> **Reboot or Log Out**: You must reboot or log out and back in for the `uinput` user group permissions to take effect. This is required for automatic pasting.

---

## How to Use

- **Configure Settings & Shortcut**: Open **VoiceDrop** from your GNOME Applications Launcher. In the settings window, you can configure the language, toggle AI grammar correction, test microphone levels, and **bind or clear your keyboard shortcut directly** using the interactive key capture interface.
- **Toggle Dictation**: Press your configured keyboard shortcut (defaults to `Super+Space`). A small blue glassmorphic visualizer dot appears at the bottom of the screen indicating it is listening.
- **Finish & Paste**: Press the shortcut again (or click the visualizer dot). The visualizer shows a spinner, transcribes and cleans the text (removing outer quotes, filler words, and corrections), pastes it directly at your text cursor, and terminates to use 0% background RAM.

---

## File Structure

- [main.py](file:///home/ncisbani/Documents/varie/VoiceDrop/main.py): Application entry point, UNIX socket server/client router.
- [config.py](file:///home/ncisbani/Documents/varie/VoiceDrop/config.py): Persistent configuration reader/writer.
- [audio_recorder.py](file:///home/ncisbani/Documents/varie/VoiceDrop/audio_recorder.py): PyAudio recorder loop.
- [transcriber.py](file:///home/ncisbani/Documents/varie/VoiceDrop/transcriber.py): Executor wrapper for `whisper.cpp` and `llama.cpp`.
- [paster.py](file:///home/ncisbani/Documents/varie/VoiceDrop/paster.py): Clipboard copy and `evdev` key injection.
- [overlay.py](file:///home/ncisbani/Documents/varie/VoiceDrop/overlay.py): Borderless glassmorphic drawing overlay.
- [settings_gui.py](file:///home/ncisbani/Documents/varie/VoiceDrop/settings_gui.py): GTK Settings GUI.
