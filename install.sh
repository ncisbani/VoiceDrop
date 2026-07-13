#!/usr/bin/env bash
set -e

echo "=== VoiceDrop Installer ==="

# 1. Identify distro and install packages
if [ -f /etc/debian_version ]; then
    echo "Detected Debian/Ubuntu system."
    sudo apt-get update
    sudo apt-get install -y python3-pyaudio python3-evdev python3-numpy python3-gi gir1.2-gtk-3.0 git cmake build-essential wl-clipboard libnotify-bin
elif [ -f /etc/fedora-release ]; then
    echo "Detected Fedora system."
    sudo dnf install -y python3-pyaudio python3-evdev python3-numpy python3-gobject git cmake gcc-c++ wl-clipboard libnotify
elif [ -f /etc/arch-release ]; then
    echo "Detected Arch Linux system."
    sudo pacman -S --needed python-pyaudio python-evdev python-numpy python-gobject git cmake gcc wl-clipboard libnotify
else
    echo "Unknown distribution. Please ensure you have python3, git, cmake, gcc/g++, wl-clipboard, libnotify, and PyGObject installed."
fi

# 2. Setup installation directory
INSTALL_DIR="$HOME/.local/share/voicedrop"
echo "Installing to $INSTALL_DIR..."

if [ -d "$INSTALL_DIR" ]; then
    echo "Directory exists. Updating..."
    cd "$INSTALL_DIR"
    git pull
else
    git clone https://github.com/ncisbani/VoiceDrop.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# 3. Setup submodules if missing
if [ ! -d "whisper.cpp/.git" ]; then
    echo "Cloning whisper.cpp..."
    rm -rf whisper.cpp
    git clone --depth 1 https://github.com/ggerganov/whisper.cpp.git whisper.cpp
fi

if [ ! -d "llama.cpp/.git" ]; then
    echo "Cloning llama.cpp..."
    rm -rf llama.cpp
    git clone --depth 1 https://github.com/ggerganov/llama.cpp.git llama.cpp
fi

# 4. Compile Engines
echo "Compiling whisper.cpp..."
cd whisper.cpp
cmake -B build -DWHISPER_BUILD_TESTS=OFF -DWHISPER_BUILD_EXAMPLES=ON
cmake --build build --config Release -j$(nproc)
cd ..

echo "Compiling llama.cpp..."
cd llama.cpp
cmake -B build -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=ON
cmake --build build --config Release -j$(nproc)
cd ..

# 5. Download models
echo "Downloading lightweight models..."
python3 download_models.py

# 6. Configure uinput permissions for auto-paste
echo "Configuring uinput permissions..."
sudo tee /etc/udev/rules.d/99-uinput.rules > /dev/null <<'EOF'
KERNEL=="uinput", GROUP="input", MODE="0660"
EOF
sudo usermod -aG input $USER
sudo modprobe uinput
sudo udevadm control --reload-rules
sudo udevadm trigger

# 7. Create desktop launcher entry
echo "Creating desktop entry..."
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/voicedrop.desktop" <<EOF
[Desktop Entry]
Name=VoiceDrop
Comment=Minimal local speech-to-text dictation settings
Exec=python3 $INSTALL_DIR/main.py
Icon=preferences-desktop-keyboard
Type=Application
Categories=Utility;Settings;
Terminal=false
StartupNotify=true
EOF
chmod +x "$HOME/.local/share/applications/voicedrop.desktop"

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

echo "=== Installation Complete ==="
echo "Note: You MUST log out and log back in (or reboot) for user group changes (input group for uinput) to take effect!"
