#!/usr/bin/env bash
set -e

echo "=== VoiceDrop macOS Installer ==="

INSTALL_DIR="$HOME/.local/share/voicedrop"
PREFERRED_BIN_DIR="$INSTALL_DIR/prebuilt/macos"
EXTERNAL_PREBUILT_DIR="${VOICEDROP_PREBUILT_DIR:-}"

if ! command -v brew >/dev/null 2>&1; then
    echo "Homebrew is required: https://brew.sh"
    exit 1
fi

brew install python cmake git portaudio curl

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

python3 -m pip install --user pyaudio numpy

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
    cmake --build whisper.cpp/build --config Release --target whisper-server -j"$(sysctl -n hw.logicalcpu)"

    echo "Building llama-server..."
    cmake -S llama.cpp -B llama.cpp/build -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=ON
    cmake --build llama.cpp/build --config Release --target llama-server -j"$(sysctl -n hw.logicalcpu)"
fi

echo "Downloading models..."
python3 download_models.py

mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/voicedrop-toggle" <<EOF
#!/usr/bin/env bash
python3 "$INSTALL_DIR/main.py" --toggle
EOF
chmod +x "$HOME/.local/bin/voicedrop-toggle"

echo "Install complete."
echo "Run dictation: ~/.local/bin/voicedrop-toggle"
echo "Tip: grant Accessibility permission to Terminal/iTerm for auto-paste."
