#!/usr/bin/env bash
set -e

echo "=== VoiceDrop Linux Uninstaller ==="
INSTALL_DIR="$HOME/.local/share/voicedrop"

read -r -p "Remove VoiceDrop and local models? (y/N) " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

pkill -f "main.py --toggle" 2>/dev/null || true
pkill -f "whisper-server.*8178" 2>/dev/null || true
pkill -f "llama-server.*8179" 2>/dev/null || true
rm -f /tmp/voicedrop.sock

rm -f "$HOME/.local/bin/voicedrop-toggle"
rm -f "$HOME/.local/share/applications/voicedrop.desktop"
rm -rf "$HOME/.config/voicedrop"
rm -rf "$INSTALL_DIR"

echo "VoiceDrop removed."
