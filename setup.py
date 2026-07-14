#!/usr/bin/env python3

import argparse
import platform
import subprocess
import sys
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def detect_platform():
    system = platform.system().lower()
    if system.startswith("windows"):
        return "windows"
    if system == "darwin":
        return "macos"
    return "linux"


def run_command(command, cwd=None, env=None):
    print(f"Running: {' '.join(command)}")
    subprocess.run(command, cwd=cwd, env=env, check=True)


def choose_mode(default_platform):
    print("VoiceDrop setup")
    print(f"Detected platform: {default_platform}")
    print("1) Install")
    print("2) Uninstall")
    choice = input("Select an option [1]: ").strip() or "1"
    return "uninstall" if choice == "2" else "install"


def install(args, target_platform):
    env = os.environ.copy()
    if args.prebuilt_dir:
        env["VOICEDROP_PREBUILT_DIR"] = str(Path(args.prebuilt_dir).expanduser().resolve())

    if target_platform == "windows":
        script = ROOT / "install-windows.ps1"
        run_command([
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
        ], env=env)
        return

    script = ROOT / ("install-macos.sh" if target_platform == "macos" else "install.sh")
    run_command(["bash", str(script)], env=env)


def uninstall(args, target_platform):
    if target_platform == "windows":
        script = ROOT / "uninstall-windows.ps1"
        run_command([
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
        ])
        return

    script = ROOT / ("uninstall-macos.sh" if target_platform == "macos" else "uninstall.sh")
    run_command(["bash", str(script)])


def main():
    parser = argparse.ArgumentParser(description="VoiceDrop setup wizard")
    parser.add_argument("action", nargs="?", choices=["install", "uninstall"], help="Action to run")
    parser.add_argument("--platform", dest="platform_name", choices=["auto", "linux", "macos", "windows"], default="auto")
    parser.add_argument("--prebuilt-dir", dest="prebuilt_dir", help="Optional directory containing prebuilt whisper/llama binaries")
    args = parser.parse_args()

    target_platform = detect_platform() if args.platform_name == "auto" else args.platform_name
    action = args.action or choose_mode(target_platform)

    if action == "install":
        install(args, target_platform)
    else:
        uninstall(args, target_platform)


if __name__ == "__main__":
    main()