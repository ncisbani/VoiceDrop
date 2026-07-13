import subprocess
import time
import os

def copy_to_clipboard(text):
    """Copy text to Wayland clipboard using wl-copy for both clipboard and primary selections."""
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

    # Add a short delay to ensure the user has released the physical shortcut keys
    # (like Super, Alt, or Space) before we simulate the paste.
    time.sleep(0.4)

    try:
        capabilities = {
            ecodes.EV_KEY: [ecodes.KEY_LEFTSHIFT, ecodes.KEY_INSERT]
        }

        with evdev.UInput(capabilities, name="voicedrop-keyboard") as ui:
            # Compositor needs more than 0.1s to register the virtual device reliably
            time.sleep(0.3)

            ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 1)
            ui.syn()
            time.sleep(0.02)

            ui.write(ecodes.EV_KEY, ecodes.KEY_INSERT, 1)
            ui.syn()
            time.sleep(0.02)

            ui.write(ecodes.EV_KEY, ecodes.KEY_INSERT, 0)
            ui.syn()
            time.sleep(0.02)

            ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 0)
            ui.syn()
            time.sleep(0.05)

        print("Simulated Shift+Insert successfully.")
        return True
    except Exception as e:
        print(f"Failed to simulate paste via evdev/uinput: {e}")
        print("Please ensure your user has permission to write to /dev/uinput.")
        return False

def paste_text(text):
    """Main paste handler: copies to clipboard and attempts to simulate Shift+Insert."""
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
