# VoiceDrop Installation Links

Use these direct links to run install scripts quickly.

Preferred local setup:

```bash
python setup.py
```

If you already have prebuilt server binaries, you can pass them into the wizard:

```bash
python setup.py --prebuilt-dir /path/to/prebuilt
```

## Linux

Install:

```bash
curl -sSf https://raw.githubusercontent.com/ncisbani/VoiceDrop/main/install.sh | bash
```

Uninstall:

```bash
curl -sSf https://raw.githubusercontent.com/ncisbani/VoiceDrop/main/uninstall.sh | bash
```

## macOS

Install:

```bash
curl -sSf https://raw.githubusercontent.com/ncisbani/VoiceDrop/main/install-macos.sh | bash
```

Uninstall:

```bash
curl -sSf https://raw.githubusercontent.com/ncisbani/VoiceDrop/main/uninstall-macos.sh | bash
```

## Windows (PowerShell)

Install:

```powershell
iwr https://raw.githubusercontent.com/ncisbani/VoiceDrop/main/install-windows.ps1 -UseBasicParsing | iex
```

Uninstall:

```powershell
iwr https://raw.githubusercontent.com/ncisbani/VoiceDrop/main/uninstall-windows.ps1 -UseBasicParsing | iex
```
