import subprocess
import time
import os

def clean_outer_quotes(text):
    if not text:
        return text
    s = text.strip()
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1].strip()
    elif s.startswith("'") and s.endswith("'"):
        s = s[1:-1].strip()
    elif s.startswith('"') and s.endswith('".'):
        s = s[1:-2].strip() + "."
    elif s.startswith('"') and s.endswith('."'):
        s = s[1:-1].strip()
    elif s.startswith("'") and s.endswith("'."):
        s = s[1:-2].strip() + "."
    elif s.startswith("'") and s.endswith(".'"):
        s = s[1:-1].strip()
    return s

def copy_to_clipboard(text):
    """Copy text to Wayland clipboard using wl-copy for both clipboard and primary selections."""
    text = clean_outer_quotes(text)
    try:
        # Copy to CLIPBOARD
        subprocess.run(["wl-copy"], input=text, text=True, check=True)
        # Copy to PRIMARY (middle-click buffer, needed for terminal Shift+Insert)
        subprocess.run(["wl-copy", "--primary"], input=text, text=True, check=True)
        print("Text successfully copied to clipboard and primary via wl-copy.")
        return True
    except Exception as e:
        print(f"Error copying to clipboard: {e}")
        return False

_uinput_device = None

def get_uinput_device():
    global _uinput_device
    if _uinput_device is None:
        try:
            import evdev
            from evdev import ecodes
            capabilities = {
                ecodes.EV_KEY: [ecodes.KEY_LEFTSHIFT, ecodes.KEY_INSERT]
            }
            _uinput_device = evdev.UInput(capabilities, name="voicedrop-keyboard")
            # Compositor needs time to register the virtual device (only once on first paste)
            time.sleep(0.3)
        except Exception as e:
            print(f"Failed to initialize evdev UInput device: {e}")
            _uinput_device = None
    return _uinput_device

def simulate_paste():
    """Simulate Shift+Insert key press using evdev if available, else return False."""
    try:
        import evdev
        from evdev import ecodes
    except ImportError:
        print("python-evdev is not installed. Skipping automatic paste simulation.")
        return False

    if not os.path.exists("/dev/uinput"):
        print("ERROR: /dev/uinput missing. Run: sudo modprobe uinput")
        return False

    if not os.access("/dev/uinput", os.W_OK):
        print("ERROR: no write permission on /dev/uinput. Fix udev rule + input group (see README).")
        return False

    # Short delay to ensure the user has released the physical shortcut keys
    time.sleep(0.15)

    ui = get_uinput_device()
    if ui is None:
        return False

    try:
        ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 1)
        ui.syn()
        time.sleep(0.01)

        ui.write(ecodes.EV_KEY, ecodes.KEY_INSERT, 1)
        ui.syn()
        time.sleep(0.01)

        ui.write(ecodes.EV_KEY, ecodes.KEY_INSERT, 0)
        ui.syn()
        time.sleep(0.01)

        ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 0)
        ui.syn()
        time.sleep(0.01)

        print("Simulated Shift+Insert successfully.")
        return True
    except Exception as e:
        print(f"Failed to simulate paste via evdev/uinput: {e}")
        return False

def paste_text(text):
    """Main paste handler: copies to clipboard and attempts to simulate Shift+Insert."""
    text = clean_outer_quotes(text)
    copied = copy_to_clipboard(text)
    if not copied:
        return False
        
    pasted = simulate_paste()
    if not pasted:
        # Fallback: Send a desktop notification
        try:
            # Try to send notification
            subprocess.run([
                "notify-send", 
                "VoiceDrop", 
                "Text copied to clipboard! Press Ctrl+V or Shift+Insert to paste.", 
                "-i", "accessories-character-map", 
                "-t", "4000"
            ])
        except Exception:
            pass
            
    return pasted
