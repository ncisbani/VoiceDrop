# Prebuilt Binaries

VoiceDrop can use prebuilt local server binaries instead of compiling `whisper.cpp` and `llama.cpp` during install.

Supported layouts:

- Linux: `prebuilt/linux/whisper-server` and `prebuilt/linux/llama-server`
- macOS: `prebuilt/macos/whisper-server` and `prebuilt/macos/llama-server`
- Windows: `prebuilt/windows/whisper-server.exe` and `prebuilt/windows/llama-server.exe`

You can also point the setup wizard at an external folder:

```bash
python setup.py --prebuilt-dir /path/to/prebuilt
```

If the binaries are missing, the installers automatically fall back to building from source.
