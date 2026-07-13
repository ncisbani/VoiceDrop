# VoiceDrop Fix Instructions

Apply each fix below exactly. File paths are relative to repo root
(`~/.local/share/voicedrop`).

---

## Fix 1 — Missing GTK3 typelib package (install.sh)

**Bug:** Debian/Ubuntu branch installs `python3-gi` (bindings) but not
`gir1.2-gtk-3.0` (the introspection data GTK bindings need at runtime).
Result: `ValueError: Namespace Gtk not available`.

**File:** `install.sh`

Find:
```bash
elif [ -f /etc/debian_version ]; then
    echo "Detected Debian/Ubuntu system."
    sudo apt-get update
    sudo apt-get install -y python3-pyaudio python3-evdev python3-numpy python3-gi git cmake build-essential wl-clipboard libnotify-bin
```

Replace with:
```bash
elif [ -f /etc/debian_version ]; then
    echo "Detected Debian/Ubuntu system."
    sudo apt-get update
    sudo apt-get install -y python3-pyaudio python3-evdev python3-numpy python3-gi gir1.2-gtk-3.0 git cmake build-essential wl-clipboard libnotify-bin
```

---

## Fix 2 — Dead SmolLM2 model URL (download_models.py)

**Bug:** `HuggingFaceTB/SmolLM2-135M-Instruct-GGUF` returns HTTP 401 on
direct resolve. Swap to a public mirror with the same quant.

**File:** `download_models.py`

Find:
```python
    "smollm-135m": {
        "url": "https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct-GGUF/resolve/main/smollm2-135m-instruct-q4_k_m.gguf",
        "path": os.path.join(MODELS_DIR, "smollm2-135m-instruct-q4_k_m.gguf")
    }
```

Replace with:
```python
    "smollm-135m": {
        "url": "https://huggingface.co/QuantFactory/SmolLM2-135M-Instruct-GGUF/resolve/main/SmolLM2-135M-Instruct.Q4_K_M.gguf",
        "path": os.path.join(MODELS_DIR, "smollm2-135m-instruct-q4_k_m.gguf")
    }
```

Note: local filename stays the same, so `config.py` default path still
matches. No change needed there.

---

## Fix 3 — Mic-test teardown race condition (settings_gui.py)

**Bug:** `stop_mic_test` kills PyAudio (`cleanup()` → `p.terminate()`)
without joining the recording thread first. Thread may still be inside
`stream.read()` when terminated — crash / corrupted PortAudio state risk.

**File:** `settings_gui.py`

Find:
```python
    def stop_mic_test(self):
        self.is_testing_mic = False
        if self.test_timer_id:
            GLib.source_remove(self.test_timer_id)
            self.test_timer_id = None
        if self.recorder:
            self.recorder.recording = False
            self.recorder.cleanup()
            self.recorder = None
        self.mic_level_bar.set_value(0.0)
```

Replace with:
```python
    def stop_mic_test(self):
        self.is_testing_mic = False
        if self.test_timer_id:
            GLib.source_remove(self.test_timer_id)
            self.test_timer_id = None
        if self.recorder:
            self.recorder.recording = False
            if self.recorder.thread:
                self.recorder.thread.join(timeout=1.0)
            self.recorder.cleanup()
            self.recorder = None
        self.mic_level_bar.set_value(0.0)
```

---

## Fix 4 — Silent mic-test failure (settings_gui.py)

**Bug:** `toggle_mic_test`'s try/except never catches real audio errors —
`AudioRecorder.start()` spawns a thread and never raises; failures happen
silently inside `_record_loop`. UI shows "Stop Test" with a dead mic and
no feedback.

**File:** `audio_recorder.py`

Find:
```python
    def _record_loop(self):
        try:
            stream = self.p.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size
            )
        except Exception as e:
            print(f"Error opening audio stream: {e}")
            self.recording = False
            return
```

Replace with:
```python
    def _record_loop(self):
        try:
            stream = self.p.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size
            )
        except Exception as e:
            print(f"Error opening audio stream: {e}")
            self.recording = False
            self.stream_error = str(e)
            return
```

Also add `self.stream_error = None` in `__init__`, right after
`self.thread = None`:

Find:
```python
        self.p = pyaudio.PyAudio()
        self.frames = []
        self.recording = False
        self.thread = None
```

Replace with:
```python
        self.p = pyaudio.PyAudio()
        self.frames = []
        self.recording = False
        self.thread = None
        self.stream_error = None
```

**File:** `settings_gui.py`

Find:
```python
    def update_mic_level(self):
        if not self.is_testing_mic or not self.recorder or not self.recorder.frames:
            return True
```

Replace with:
```python
    def update_mic_level(self):
        if not self.is_testing_mic or not self.recorder:
            return True
        if self.recorder.stream_error:
            print(f"Mic test failed: {self.recorder.stream_error}")
            self.stop_mic_test()
            self.test_mic_btn.set_label("Test Microphone")
            return False
        if not self.recorder.frames:
            return True
```

---

## Fix 5 — Fragile headless GTK call in install.sh step 8

**Bug:** Step 8 instantiates the full `SettingsWindow` GTK class (which
calls `show_all()` in `__init__`) just to reach two helper methods. If no
display/dbus session is present (SSH install, minimal environment), this
crashes the whole install (`set -e` is active) even after a successful
build.

**File:** `settings_gui.py`

Add these two module-level functions near the top of the file, after the
imports (do not remove the `SettingsWindow` class — keep it as is):

```python
def get_custom_bindings_headless():
    import subprocess, ast
    try:
        out = subprocess.check_output(
            ["gsettings", "get", "org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings"],
            text=True
        ).strip()
        if not out or out == "@as []" or out == "[]":
            return []
        if out.startswith("@as "):
            out = out[4:]
        return ast.literal_eval(out)
    except Exception:
        return []

def find_voicedrop_shortcut_headless():
    import subprocess
    paths = get_custom_bindings_headless()
    for path in paths:
        try:
            name = subprocess.check_output(
                ["gsettings", "get", f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{path}", "name"],
                text=True
            ).strip().strip("'\"")
            cmd = subprocess.check_output(
                ["gsettings", "get", f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{path}", "command"],
                text=True
            ).strip().strip("'\"")
            binding = subprocess.check_output(
                ["gsettings", "get", f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{path}", "binding"],
                text=True
            ).strip().strip("'\"")
            if "voicedrop" in name.lower() or "voicedrop" in cmd.lower():
                return path, name, cmd, binding
        except Exception:
            continue
    return None, None, None, None

def save_voicedrop_shortcut_headless(binding_str, install_dir):
    import subprocess, os
    path, name, cmd, old_binding = find_voicedrop_shortcut_headless()
    app_path = os.path.join(install_dir, "main.py")
    target_cmd = f"/usr/bin/python3 {app_path} --toggle"

    if not binding_str:
        if path:
            paths = get_custom_bindings_headless()
            if path in paths:
                paths.remove(path)
                val = "[" + ", ".join(f"'{p}'" for p in paths) + "]" if paths else "@as []"
                subprocess.run(["gsettings", "set", "org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings", val], check=True)
        return True

    if path:
        subprocess.run(["gsettings", "set", f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{path}", "binding", f"'{binding_str}'"], check=True)
        subprocess.run(["gsettings", "set", f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{path}", "command", f"'{target_cmd}'"], check=True)
        return True
    else:
        paths = get_custom_bindings_headless()
        idx = 0
        while True:
            new_path = f"/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom{idx}/"
            if new_path not in paths:
                break
            idx += 1
        paths.append(new_path)
        val = "[" + ", ".join(f"'{p}'" for p in paths) + "]"
        subprocess.run(["gsettings", "set", "org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings", val], check=True)
        subprocess.run(["gsettings", "set", f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{new_path}", "name", "'VoiceDrop'"], check=True)
        subprocess.run(["gsettings", "set", f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{new_path}", "command", f"'{target_cmd}'"], check=True)
        subprocess.run(["gsettings", "set", f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{new_path}", "binding", f"'{binding_str}'"], check=True)
        return True
```

**File:** `install.sh`

Find:
```bash
# 8. Setup default keyboard shortcut
echo "Setting up default keyboard shortcut (<Super>space)..."
python3 -c "
import sys
sys.path.append('$INSTALL_DIR')
import settings_gui
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
win = settings_gui.SettingsWindow()
# Bind default if not already bound
path, _, _, current = win.find_voicedrop_shortcut()
if not current:
    win.save_voicedrop_shortcut('<Super>space')
    print('Default shortcut bound to Super+Space.')
else:
    print(f'VoiceDrop shortcut already bound to: {current}')
"
```

Replace with:
```bash
# 8. Setup default keyboard shortcut
echo "Setting up default keyboard shortcut (<Super>space)..."
python3 -c "
import sys
sys.path.append('$INSTALL_DIR')
import settings_gui
path, _, _, current = settings_gui.find_voicedrop_shortcut_headless()
if not current:
    settings_gui.save_voicedrop_shortcut_headless('<Super>space', '$INSTALL_DIR')
    print('Default shortcut bound to Super+Space.')
else:
    print(f'VoiceDrop shortcut already bound to: {current}')
"
```

This drops the GTK/display dependency entirely from the install step —
pure `gsettings` + `subprocess`, works headless.

---

## After applying

Re-run:
```bash
curl -sSf https://raw.githubusercontent.com/ncisbani/VoiceDrop/main/install.sh | bash
```
(or `git pull` in `~/.local/share/voicedrop` then re-run `install.sh`
locally if you've modified it directly, since curl pulls the remote
version — apply these fixes to your local clone and run `./install.sh`
from inside it instead of curling, or push the fixes to your fork first.)
