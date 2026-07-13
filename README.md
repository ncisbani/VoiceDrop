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

### 1. Install Keyboard Simulation (Optional, for Auto-Pasting)
To allow VoiceDrop to automatically paste the text, you need the `evdev` python package.
Run the following command in your terminal:
```bash
sudo dnf install -y python3-evdev
```
*Note: You must also grant your user write access to `/dev/uinput`. Run once, then reboot:*

```bash
sudo tee /etc/udev/rules.d/99-uinput.rules > /dev/null <<'EOF'
KERNEL=="uinput", GROUP="input", MODE="0660"
EOF
sudo usermod -aG input $USER
sudo modprobe uinput
sudo udevadm control --reload-rules
sudo udevadm trigger
```

*Reboot or fully log out/in — group membership requires a new session. Verify with `ls -l /dev/uinput` (should show group `input`) and `groups` (should list `input`).*

### 2. Configure GNOME Keyboard Shortcut
To trigger VoiceDrop with a keyboard shortcut (e.g., `Super+Space` or `Alt+S`):
1. Open **Settings** → **Keyboard** → **Keyboard Shortcuts**.
2. Scroll to the bottom and select **Custom Shortcuts**.
3. Click the **+** button to add a new shortcut:
   - **Name**: `VoiceDrop Dictation`
   - **Command**: `python3 /home/ncisbani/Documents/varie/VoiceDrop/main.py --toggle`
   - **Shortcut**: Press your preferred key combination (e.g., `Super+Space` or `Alt+S`).
4. Click **Add**.

---

## How to Use

- **Toggle Dictation**: Press your configured keyboard shortcut. The small glassmorphic visualizer will appear at the bottom-center of the screen, animating to your voice.
- **Finish & Paste**: Press the shortcut again (or click directly on the visualizer bubble). The visualizer will show "Processing...", transcribe and clean up the speech, and automatically paste it at your text cursor.
- **Configure Settings**: Open the **VoiceDrop** application from your GNOME Applications Launcher, or run:
  ```bash
  python3 /home/ncisbani/Documents/varie/VoiceDrop/main.py
  ```
  In settings, you can change the language (English, Italian, Spanish, French, German), toggle AI grammar correction, change Whisper/LLM models, and test your microphone input levels.

---

## File Structure

- [main.py](file:///home/ncisbani/Documents/varie/VoiceDrop/main.py): Application entry point, UNIX socket server/client router.
- [config.py](file:///home/ncisbani/Documents/varie/VoiceDrop/config.py): Persistent configuration reader/writer.
- [audio_recorder.py](file:///home/ncisbani/Documents/varie/VoiceDrop/audio_recorder.py): PyAudio recorder loop.
- [transcriber.py](file:///home/ncisbani/Documents/varie/VoiceDrop/transcriber.py): Executor wrapper for `whisper.cpp` and `llama.cpp`.
- [paster.py](file:///home/ncisbani/Documents/varie/VoiceDrop/paster.py): Clipboard copy and `evdev` key injection.
- [overlay.py](file:///home/ncisbani/Documents/varie/VoiceDrop/overlay.py): Borderless glassmorphic drawing overlay.
- [settings_gui.py](file:///home/ncisbani/Documents/varie/VoiceDrop/settings_gui.py): GTK Settings GUI.
