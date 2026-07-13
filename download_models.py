import os
import sys
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

# URL mappings
MODELS = {
    "whisper-tiny": {
        "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin",
        "path": os.path.join(MODELS_DIR, "ggml-tiny.bin")
    },
    "smollm-135m": {
        "url": "https://huggingface.co/QuantFactory/SmolLM2-135M-Instruct-GGUF/resolve/main/SmolLM2-135M-Instruct.Q4_K_M.gguf",
        "path": os.path.join(MODELS_DIR, "smollm2-135m-instruct-q4_k_m.gguf")
    }
}

def report_progress(block_num, block_size, total_size):
    read_so_far = block_num * block_size
    if total_size > 0:
        percent = read_so_far * 1e2 / total_size
        s = f"\rDownloading... {percent:5.1f}% [{read_so_far / 1024 / 1024:.1f} MB / {total_size / 1024 / 1024:.1f} MB]"
        sys.stdout.write(s)
        sys.stdout.flush()
    else:
        sys.stdout.write(f"\rDownloading... {read_so_far / 1024 / 1024:.1f} MB")
        sys.stdout.flush()

def download_model(name):
    info = MODELS[name]
    url = info["url"]
    path = info["path"]
    
    if os.path.exists(path):
        print(f"{name} model already exists at {path}.")
        return
        
    print(f"Downloading {name} model from {url}...")
    try:
        urllib.request.urlretrieve(url, path, report_progress)
        print(f"\nSuccessfully downloaded {name} to {path}!")
    except Exception as e:
        print(f"\nError downloading {name}: {e}")
        if os.path.exists(path):
            os.remove(path)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        model_to_download = sys.argv[1]
        if model_to_download in MODELS:
            download_model(model_to_download)
        else:
            print(f"Unknown model: {model_to_download}")
    else:
        for model_name in MODELS:
            download_model(model_name)
