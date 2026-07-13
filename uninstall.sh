#!/usr/bin/env bash
set -e

echo "=== VoiceDrop Uninstaller (unstable) ==="
echo "This will remove ALL VoiceDrop files, configs, compiled engines, and system integrations."
echo "This cannot be undone."
echo ""

read -p "Continue? (y/N) " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

INSTALL_DIR="$HOME/.local/share/voicedrop"

# 1. Kill any running daemon
echo "Stopping running daemon (if any)..."
pkill -f "voicedrop" 2>/dev/null || true
rm -f /tmp/voicedrop.sock

# 2. Remove desktop entry
echo "Removing desktop entry..."
rm -f "$HOME/.local/share/applications/voicedrop.desktop"

# 3. Remove GNOME keybinding
echo "Removing keyboard shortcut..."
python3 -c "
import subprocess, ast
try:
    out = subprocess.check_output(
        ['gsettings', 'get', 'org.gnome.settings-daemon.plugins.media-keys', 'custom-keybindings'],
        text=True
    ).strip()
    if not out or out == '@as []' or out == '[]':
        exit(0)
    if out.startswith('@as '):
        out = out[4:]
    paths = ast.literal_eval(out)
except Exception:
    exit(0)

for path in paths:
    try:
        name = subprocess.check_output(
            ['gsettings', 'get', f'org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{path}', 'name'],
            text=True
        ).strip().strip(\"'\")
        cmd = subprocess.check_output(
            ['gsettings', 'get', f'org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{path}', 'command'],
            text=True
        ).strip().strip(\"'\")
        if 'voicedrop' in name.lower() or 'voicedrop' in cmd.lower():
            paths.remove(path)
            subprocess.run(['gsettings', 'reset-recursively', f'org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{path}'], stderr=subprocess.DEVNULL)
            val = '[' + ', '.join(f\"'{p}'\" for p in paths) + ']' if paths else '@as []'
            subprocess.run(['gsettings', 'set', 'org.gnome.settings-daemon.plugins.media-keys', 'custom-keybindings', val], check=True)
            print(f'Removed shortcut at {path}')
            break
    except Exception:
        continue
" 2>/dev/null || echo "Failed to remove shortcut (may need manual cleanup)"

# 4. Remove udev rule and input group
echo "Removing uinput permissions..."
sudo rm -f /etc/udev/rules.d/99-uinput.rules
sudo usermod -dG input "$USER" 2>/dev/null || true
sudo udevadm control --reload-rules 2>/dev/null || true
sudo udevadm trigger 2>/dev/null || true

# 5. Remove config
echo "Removing config..."
rm -rf "$HOME/.config/voicedrop"

# 6. Remove install directory (compiled engines + models + source)
echo "Removing install directory: $INSTALL_DIR"
rm -rf "$INSTALL_DIR"

echo ""
echo "=== VoiceDrop uninstalled ==="
echo "You may need to log out and back in for group changes to take effect."
