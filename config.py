import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_config_dir():
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return os.path.join(appdata, "VoiceDrop")
        return os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "VoiceDrop")

    if os.uname().sysname == "Darwin":
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", "VoiceDrop")

    return os.path.expanduser("~/.config/voicedrop")

CONFIG_DIR = get_config_dir()
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "language": "en",
    "whisper_model": os.path.join(BASE_DIR, "models/ggml-tiny.bin"),
    "llm_model": os.path.join(BASE_DIR, "models/smollm2-135m-instruct-q4_k_m.gguf"),
    "llm_correction": True,
    "auto_paste": True,
    "audio_device_index": None
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            # Ensure all default keys exist
            updated = False
            for k, v in DEFAULT_CONFIG.items():
                if k not in config:
                    config[k] = v
                    updated = True
            
            # Migration/validation: if model path doesn't exist, is old/heavy, or has wrong base path, reset it
            for key in ["whisper_model", "llm_model"]:
                path = config.get(key)
                if not path or "ggml-base.bin" in path or "qwen2.5-0.5b" in path or not os.path.exists(path):
                    config[key] = DEFAULT_CONFIG[key]
                    updated = True
            
            if updated:
                save_config(config)
            return config
    except Exception as e:
        print(f"Error loading config, using defaults: {e}")
        return DEFAULT_CONFIG

def save_config(config):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")
