import subprocess
import json

WHISPER_SERVER_URL = "http://127.0.0.1:8178"
LLAMA_SERVER_URL = "http://127.0.0.1:8179"

class Transcriber:
    def __init__(self, whisper_server_url=WHISPER_SERVER_URL, llama_server_url=LLAMA_SERVER_URL):
        self.whisper_server_url = whisper_server_url
        self.llama_server_url = llama_server_url

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

    def transcribe(self, wav_path, language="en"):
        cmd = [
            "curl", "-sS", "-X", "POST",
            f"{self.whisper_server_url}/inference",
            "-F", f"file=@{wav_path}",
            "-F", f"language={language}",
            "-F", "response_format=json"
        ]
        print(f"Requesting transcription from whisper-server: {wav_path}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"Could not reach whisper-server at {self.whisper_server_url}: {result.stderr.strip()}\n"
                f"Check it's running: systemctl --user status voicedrop-whisper"
            )
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            raise RuntimeError(f"whisper-server returned invalid response: {result.stdout[:200]}")
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

        payload = json.dumps({
            "prompt": prompt,
            "n_predict": 256,
            "temperature": 0.1,
            "stop": ["<|im_end|>"]
        })

        cmd = [
            "curl", "-sS", "-X", "POST",
            f"{self.llama_server_url}/completion",
            "-H", "Content-Type: application/json",
            "-d", payload
        ]
        print("Requesting correction from llama-server")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print(f"Could not reach llama-server at {self.llama_server_url}: {result.stderr.strip()}")
            print("Check it's running: systemctl --user status voicedrop-llama")
            return raw_text

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"llama-server returned invalid response: {result.stdout[:200]}")
            return raw_text

        corrected = data.get("content", "").strip()
        final_text = corrected if corrected else raw_text
        final_text = self._strip_outer_quotes(final_text)

        print(f"Final polished transcription: {final_text}")
        return final_text
