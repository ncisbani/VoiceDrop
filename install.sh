#!/usr/bin/env bash
set -e

echo "=== VoiceDrop Installer ==="

# 1. Identify distro and install packages
if [ -f /etc/debian_version ]; then
    echo "Detected Debian/Ubuntu system."
    sudo apt-get update
    sudo apt-get install -y python3-pyaudio python3-numpy python3-gi gir1.2-gtk-3.0 git cmake build-essential wl-clipboard libnotify-bin ydotool
elif [ -f /etc/fedora-release ]; then
    echo "Detected Fedora system."
    sudo dnf install -y python3-pyaudio python3-numpy python3-gobject git cmake gcc-c++ wl-clipboard libnotify ydotool
elif [ -f /etc/arch-release ]; then
    echo "Detected Arch Linux system."
    sudo pacman -S --needed python-pyaudio python-numpy python-gobject git cmake gcc wl-clipboard libnotify ydotool
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
    git clone --depth 1 https://github.com/ncisbani/VoiceDrop.git "$INSTALL_DIR"
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

# 4. Compile Engines (server binaries only — see PART 2 of fix notes)
echo "Compiling whisper.cpp..."
cd whisper.cpp
cmake -B build -DWHISPER_BUILD_TESTS=OFF -DWHISPER_BUILD_EXAMPLES=ON
cmake --build build --config Release -j$(nproc) --target whisper-server
cd ..

echo "Compiling llama.cpp..."
cd llama.cpp
cmake -B build -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=ON
cmake --build build --config Release -j$(nproc) --target llama-server
cd ..

# 5. Download models
echo "Downloading lightweight models..."
python3 download_models.py

# 5b. Set up persistent model servers (systemd user services)
echo "Setting up whisper-server and llama-server as background services..."
mkdir -p "$HOME/.config/systemd/user"

cat > "$HOME/.config/systemd/user/voicedrop-whisper.service" <<EOF
[Unit]
Description=VoiceDrop Whisper STT Server
After=network.target

[Service]
ExecStart=$INSTALL_DIR/whisper.cpp/build/bin/whisper-server -m $INSTALL_DIR/models/ggml-tiny.bin --host 127.0.0.1 --port 8178
Restart=on-failure
RestartSec=2

[Install]
WantedBy=default.target
EOF

cat > "$HOME/.config/systemd/user/voicedrop-llama.service" <<EOF
[Unit]
Description=VoiceDrop Llama Correction Server
After=network.target

[Service]
ExecStart=$INSTALL_DIR/llama.cpp/build/bin/llama-server -m $INSTALL_DIR/models/smollm2-135m-instruct-q4_k_m.gguf --host 127.0.0.1 --port 8179 -ngl 0 -c 2048
Restart=on-failure
RestartSec=2

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now voicedrop-whisper.service voicedrop-llama.service

# 6. Configure uinput permissions and start ydotoold (needed for auto-paste)
echo "Configuring uinput permissions for ydotool..."
sudo tee /etc/udev/rules.d/99-uinput.rules > /dev/null <<'EOF'
KERNEL=="uinput", GROUP="input", MODE="0660"
EOF
sudo usermod -aG input $USER
sudo modprobe uinput
sudo udevadm control --reload-rules
sudo udevadm trigger

mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/ydotoold.service" <<EOF
[Unit]
Description=ydotool daemon (virtual input for VoiceDrop paste)
After=default.target

[Service]
ExecStart=$(command -v ydotoold) --socket-path=%t/.ydotool_socket
Restart=on-failure
RestartSec=2

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now ydotoold.service

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
echo "Setting up default keyboard shortcut (<Shift>space)..."
python3 -c "
import sys
sys.path.append('$INSTALL_DIR')
import settings_gui
path, _, _, current = settings_gui.find_voicedrop_shortcut_headless()
if not current:
    settings_gui.save_voicedrop_shortcut_headless('<Shift>space', '$INSTALL_DIR')
    print('Default shortcut bound to Shift+Space.')
else:
    print(f'VoiceDrop shortcut already bound to: {current}')
"

echo "=== Installation Complete ==="
echo "Note: You MUST log out and log back in (or reboot) for user group changes (input group for uinput) to take effect!"
