#!/usr/bin/env bash
set -e

echo "=== VoiceDrop Linux Installer ==="

INSTALL_DIR="$HOME/.local/share/voicedrop"
PREFERRED_BIN_DIR="$INSTALL_DIR/prebuilt/linux"
EXTERNAL_PREBUILT_DIR="${VOICEDROP_PREBUILT_DIR:-}"

if [ -f /etc/debian_version ]; then
    sudo apt-get update
    sudo apt-get install -y python3 python3-pyaudio python3-numpy python3-gi gir1.2-gtk-3.0 git cmake build-essential curl
    sudo apt-get install -y wl-clipboard libnotify-bin ydotool || true
elif [ -f /etc/fedora-release ]; then
    sudo dnf install -y python3 python3-pyaudio python3-numpy python3-gobject git cmake gcc-c++ curl
    sudo dnf install -y wl-clipboard libnotify ydotool || true
elif [ -f /etc/arch-release ]; then
    sudo pacman -S --needed --noconfirm python python-pyaudio python-numpy python-gobject git cmake gcc curl
    sudo pacman -S --needed --noconfirm wl-clipboard libnotify ydotool || true
else
    echo "Unknown distro: install Python3, PyAudio, NumPy, PyGObject, git, cmake, and a C++ compiler manually."
fi

if [ -d "$INSTALL_DIR/.git" ]; then
    cd "$INSTALL_DIR"
    git pull
else
    git clone --depth 1 https://github.com/ncisbani/VoiceDrop.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

if [ ! -d "whisper.cpp/.git" ]; then
    rm -rf whisper.cpp
    git clone --depth 1 https://github.com/ggerganov/whisper.cpp.git whisper.cpp
fi

if [ ! -d "llama.cpp/.git" ]; then
    rm -rf llama.cpp
    git clone --depth 1 https://github.com/ggerganov/llama.cpp.git llama.cpp
fi

SOURCE_PREBUILT_DIR="$PREFERRED_BIN_DIR"
if [ -n "$EXTERNAL_PREBUILT_DIR" ]; then
    SOURCE_PREBUILT_DIR="$EXTERNAL_PREBUILT_DIR"
fi

if [ -x "$SOURCE_PREBUILT_DIR/whisper-server" ] && [ -x "$SOURCE_PREBUILT_DIR/llama-server" ]; then
    echo "Using prebuilt binaries from $SOURCE_PREBUILT_DIR"
    mkdir -p whisper.cpp/build/bin llama.cpp/build/bin
    cp "$SOURCE_PREBUILT_DIR/whisper-server" whisper.cpp/build/bin/
    cp "$SOURCE_PREBUILT_DIR/llama-server" llama.cpp/build/bin/
else
    echo "Building whisper-server..."
    cmake -S whisper.cpp -B whisper.cpp/build -DWHISPER_BUILD_TESTS=OFF -DWHISPER_BUILD_EXAMPLES=ON
    cmake --build whisper.cpp/build --config Release --target whisper-server -j"$(nproc)"

    echo "Building llama-server..."
    cmake -S llama.cpp -B llama.cpp/build -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=ON
    cmake --build llama.cpp/build --config Release --target llama-server -j"$(nproc)"
fi

echo "Downloading models..."
python3 download_models.py

mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/voicedrop-toggle" <<EOF
#!/usr/bin/env bash
python3 "$INSTALL_DIR/main.py" --toggle
EOF
chmod +x "$HOME/.local/bin/voicedrop-toggle"

mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/voicedrop.desktop" <<EOF
[Desktop Entry]
Name=VoiceDrop
Comment=Local lightweight speech-to-text
Exec=python3 $INSTALL_DIR/main.py
Icon=preferences-desktop-keyboard
Type=Application
Categories=Utility;AudioVideo;
Terminal=false
EOF

echo "Install complete."
echo "Run dictation: ~/.local/bin/voicedrop-toggle"
echo "Open settings: python3 $INSTALL_DIR/main.py"
