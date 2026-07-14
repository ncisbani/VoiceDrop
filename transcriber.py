import json
import uuid
import time
import atexit
import os
import socket
import subprocess
import urllib.request
import urllib.error
import config

WHISPER_SERVER_URL = "http://127.0.0.1:8178"
LLAMA_SERVER_URL = "http://127.0.0.1:8179"

class Transcriber:
    def __init__(self, whisper_server_url=WHISPER_SERVER_URL, llama_server_url=LLAMA_SERVER_URL):
        self.whisper_server_url = whisper_server_url
        self.llama_server_url = llama_server_url
        self._spawned_processes = []
        self._base_dir = os.path.dirname(os.path.abspath(__file__))
        atexit.register(self._shutdown_spawned_servers)

    def _shutdown_spawned_servers(self):
        for p in self._spawned_processes:
            try:
                p.terminate()
            except Exception:
                pass
        self._spawned_processes = []

    def _is_port_open(self, host, port, timeout=0.6):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((host, port))
            return True
        except Exception:
            return False
        finally:
            try:
                sock.close()
            except Exception:
                pass

    def _bin_name(self, base):
        if os.name == "nt":
            return f"{base}.exe"
        return base

    def _ensure_local_servers(self):
        cfg = config.load_config()
        whisper_model = cfg.get("whisper_model")
        llama_model = cfg.get("llm_model")

        whisper_bin = os.path.join(
            self._base_dir,
            "whisper.cpp",
            "build",
            "bin",
            self._bin_name("whisper-server"),
        )
        llama_bin = os.path.join(
            self._base_dir,
            "llama.cpp",
            "build",
            "bin",
            self._bin_name("llama-server"),
        )

        if not self._is_port_open("127.0.0.1", 8178):
            if not os.path.exists(whisper_bin) or not whisper_model or not os.path.exists(whisper_model):
                raise RuntimeError(
                    "whisper-server is not running and local binaries/models were not found. "
                    "Run the platform install script first."
                )
            p = subprocess.Popen(
                [whisper_bin, "-m", whisper_model, "--host", "127.0.0.1", "--port", "8178"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._spawned_processes.append(p)

        if not self._is_port_open("127.0.0.1", 8179):
            if not os.path.exists(llama_bin) or not llama_model or not os.path.exists(llama_model):
                raise RuntimeError(
                    "llama-server is not running and local binaries/models were not found. "
                    "Run the platform install script first."
                )
            p = subprocess.Popen(
                [
                    llama_bin,
                    "-m",
                    llama_model,
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8179",
                    "-ngl",
                    "0",
                    "-c",
                    "2048",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._spawned_processes.append(p)

        # Give newly started servers a moment to bind ports.
        for _ in range(20):
            if self._is_port_open("127.0.0.1", 8178) and self._is_port_open("127.0.0.1", 8179):
                return
            time.sleep(0.25)

        raise RuntimeError("Local whisper/llama servers did not start correctly.")

    def _strip_outer_quotes(self, text):
        """Strip matched outer quotes (double, single, smart) from text."""
        if not text:
            return text
        s = text.strip()
        quote_pairs = [
            ('\u201c', '\u201d'),
            ('\u2018', '\u2019'),
            ('"', '"'),
            ("'", "'"),
        ]
        for open_q, close_q in quote_pairs:
            if s.startswith(open_q) and s.endswith(close_q) and len(s) > 1:
                s = s[len(open_q):-len(close_q)].strip()
                break
        if s.endswith('.') and len(s) > 1:
            for open_q, close_q in quote_pairs:
                inner = s[:-1].strip()
                if inner.startswith(open_q) and inner.endswith(close_q) and len(inner) > 1:
                    s = inner[len(open_q):-len(close_q)].strip() + "."
                    break
        return s

    def _post_multipart(self, url, fields, file_field, file_path, timeout=120):
        boundary = f"----VoiceDropBoundary{uuid.uuid4().hex}"
        body = bytearray()

        for name, value in fields.items():
            body.extend(f"--{boundary}\r\n".encode("utf-8"))
            body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
            body.extend(str(value).encode("utf-8"))
            body.extend(b"\r\n")

        filename = file_path.split("/")[-1].split("\\")[-1]
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'.encode("utf-8")
        )
        body.extend(b"Content-Type: audio/wav\r\n\r\n")
        body.extend(file_bytes)
        body.extend(b"\r\n")
        body.extend(f"--{boundary}--\r\n".encode("utf-8"))

        req = urllib.request.Request(url, data=bytes(body), method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")

    def _post_json(self, url, payload, timeout=120):
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")

    def transcribe(self, wav_path, language="en"):
        self._ensure_local_servers()
        print(f"Requesting transcription from whisper-server: {wav_path}")
        try:
            response_text = self._post_multipart(
                f"{self.whisper_server_url}/inference",
                fields={"language": language, "response_format": "json"},
                file_field="file",
                file_path=wav_path,
                timeout=180,
            )
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            raise RuntimeError(
                f"Could not reach whisper-server at {self.whisper_server_url}: {e}\n"
                f"Check it's running: systemctl --user status voicedrop-whisper"
            )

        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            raise RuntimeError(f"whisper-server returned invalid response: {response_text[:200]}")
        if "error" in data:
            raise RuntimeError(f"whisper-server error: {data['error']}")

        transcription = self._strip_outer_quotes(data.get("text", "").strip())
        print(f"Raw transcription: {transcription}")
        return transcription

    def correct_text(self, raw_text, language="en"):
        if not raw_text.strip():
            return raw_text

        lang_names = {
            "en": "English", "it": "Italian", "es": "Spanish",
            "fr": "French", "de": "German"
        }
        lang_name = lang_names.get(language, "the same language as input")

        prompt = (
            "<|im_start|>system\n"
            "You are a speech transcription cleanup assistant. Your job is to correct grammatical mistakes, "
            "remove filler words (like 'um', 'ah', 'uh', etc.), and correct self-corrections (e.g. if the user says "
            "'I want to go on Monday... no wait, Tuesday', you should output 'I want to go on Tuesday').\n"
            "CRITICAL: Do NOT add any explanations, notes, introductory text (like 'Here is the cleaned text:'), "
            f"or markdown formatting. Only output the cleaned up, natural transcription in {lang_name}.\n"
            "<|im_end|>\n"
            "<|im_start|>user\n"
            f"Clean up this transcript: \"{raw_text}\"\n"
            "<|im_end|>\n"
            "<|im_start|>assistant\n"
        )

        payload = {
            "prompt": prompt,
            "n_predict": 256,
            "temperature": 0.1,
            "stop": ["<|im_end|>"]
        }

        print("Requesting correction from llama-server")
        try:
            response_text = self._post_json(f"{self.llama_server_url}/completion", payload, timeout=180)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            print(f"Could not reach llama-server at {self.llama_server_url}: {e}")
            print("Check it's running: systemctl --user status voicedrop-llama")
            return raw_text

        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            print(f"llama-server returned invalid response: {response_text[:200]}")
            return raw_text

        corrected = data.get("content", "").strip()
        final_text = corrected if corrected else raw_text
        final_text = self._strip_outer_quotes(final_text)

        print(f"Final polished transcription: {final_text}")
        return final_text
