#!/usr/bin/env bash
set -e

echo "=== VoiceDrop macOS Uninstaller ==="
INSTALL_DIR="$HOME/.local/share/voicedrop"

read -r -p "Remove VoiceDrop and local models? (y/N) " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

pkill -f "whisper-server.*8178" 2>/dev/null || true
pkill -f "llama-server.*8179" 2>/dev/null || true

rm -f "$HOME/.local/bin/voicedrop-toggle"
rm -rf "$HOME/Library/Application Support/VoiceDrop"
rm -rf "$INSTALL_DIR"

echo "VoiceDrop removed."
