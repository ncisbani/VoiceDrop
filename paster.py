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
        subprocess.run(["wl-copy"], input=text, text=True, check=True)
        subprocess.run(["wl-copy", "--primary"], input=text, text=True, check=True)
        print("Text successfully copied to clipboard and primary via wl-copy.")
        return True
    except Exception as e:
        print(f"Error copying to clipboard: {e}")
        return False

def get_ydotool_env():
    """ydotool talks to ydotoold over a unix socket. Match the path used
    in the systemd user unit (see install.sh)."""
    env = os.environ.copy()
    env.setdefault("YDOTOOL_SOCKET", f"/run/user/{os.getuid()}/.ydotool_socket")
    return env

def simulate_paste():
    """Simulate Shift+Insert via ydotool. Keycodes: LEFTSHIFT=42, INSERT=110
    (same linux/input-event-codes.h values the old evdev code used)."""
    time.sleep(0.15)  # let the user release the physical shortcut keys
    try:
        result = subprocess.run(
            ["ydotool", "key", "42:1", "110:1", "110:0", "42:0"],
            env=get_ydotool_env(),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if result.returncode != 0:
            print(f"ydotool paste failed: {result.stderr.strip()}")
            print("Check the daemon: systemctl --user status ydotoold")
            return False
        print("Simulated Shift+Insert successfully via ydotool.")
        return True
    except FileNotFoundError:
        print("ydotool is not installed. Skipping automatic paste simulation.")
        return False
    except Exception as e:
        print(f"Failed to simulate paste via ydotool: {e}")
        return False

def paste_text(text):
    """Main paste handler: copies to clipboard and attempts to simulate Shift+Insert."""
    text = clean_outer_quotes(text)
    copied = copy_to_clipboard(text)
    if not copied:
        return False

    pasted = simulate_paste()
    if not pasted:
        try:
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
