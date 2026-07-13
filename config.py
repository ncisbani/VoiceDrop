import os
import json

CONFIG_DIR = os.path.expanduser("~/.config/voicedrop")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "language": "en",
    "whisper_model": "/home/ncisbani/Documents/varie/VoiceDrop/models/ggml-base.bin",
    "llm_model": "/home/ncisbani/Documents/varie/VoiceDrop/models/qwen2.5-0.5b-instruct-q4_k_m.gguf",
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
