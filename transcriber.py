import subprocess
import os
import tempfile
import re

class Transcriber:
    def __init__(self, whisper_cli_path, whisper_model, llama_cli_path=None, llm_model=None):
        self.whisper_cli_path = whisper_cli_path
        self.whisper_model = whisper_model
        self.llama_cli_path = llama_cli_path
        self.llm_model = llm_model

    def transcribe(self, wav_path, language="en"):
        if not os.path.exists(self.whisper_model):
            raise FileNotFoundError(f"Whisper model not found at {self.whisper_model}")
        
        cmd = [
            self.whisper_cli_path,
            "-m", self.whisper_model,
            "-f", wav_path,
            "-nt", # No timestamps
            "-l", language
        ]
        
        print(f"Running Whisper STT command: {' '.join(cmd)}")
        # Run whisper-cli and capture stdout and stderr
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        
        if result.returncode != 0:
            print(f"Whisper error: {result.stderr}")
            raise RuntimeError(f"Whisper failed: {result.stderr}")
            
        # Clean up whisper output (remove empty lines, leading/trailing spaces)
        raw_text = result.stdout.strip()
        
        # Whisper sometimes includes brackets or comments like [music] or [whispering], let's keep them but strip newlines
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        transcription = " ".join(lines)
        
        print(f"Raw transcription: {transcription}")
        return transcription

    def correct_text(self, raw_text, language="en"):
        if not self.llama_cli_path or not self.llm_model:
            return raw_text
            
        if not os.path.exists(self.llm_model):
            print(f"LLM model not found at {self.llm_model}, skipping correction.")
            return raw_text
            
        if not raw_text.strip():
            return raw_text

        # Map language code to full name for the prompt
        lang_names = {
            "en": "English",
            "it": "Italian",
            "es": "Spanish",
            "fr": "French",
            "de": "German"
        }
        lang_name = lang_names.get(language, "the same language as input")

        # Construct ChatML prompt
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

        # Write prompt to a temp file to avoid shell escaping issues
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(prompt)
            temp_file_path = temp_file.name

        cmd = [
            self.llama_cli_path,
            "-m", self.llm_model,
            "-f", temp_file_path,
            "-n", "256",            # limit output tokens
            "--temp", "0.1",        # low temperature for consistency
            "-ngl", "0",            # cpu execution
            "-st",                  # single-turn only (prevents interactive hang)
            "--simple-io"           # basic IO for subprocess redirection compatibility
        ]

        print(f"Running LLM correction command: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        finally:
            # Clean up the temp file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        if result.returncode != 0:
            print(f"Llama CLI error: {result.stderr}")
            return raw_text  # Fallback to raw text on error

        output = result.stdout
        
        # Parse the output backwards to extract the generated completion.
        # This isolates the clean response from the ASCII logo, commands list, truncated prompts, and stats.
        lines = output.splitlines()
        stats_idx = -1
        for i, line in enumerate(lines):
            if "[ Prompt: " in line:
                stats_idx = i
                break

        corrected = ""
        if stats_idx != -1:
            prompt_end_idx = -1
            # Walk backwards from the stats block to find the end of the prompt display
            for j in range(stats_idx - 1, -1, -1):
                line = lines[j]
                if "(truncated)" in line or "<|im_start|>assistant" in line:
                    prompt_end_idx = j
                    break
            
            # Fallback: look for the last line starting with the user/system prompt symbol ">"
            if prompt_end_idx == -1:
                for j in range(stats_idx - 1, -1, -1):
                    if lines[j].strip().startswith(">"):
                        prompt_end_idx = j
                        break

            if prompt_end_idx != -1:
                generated_lines = lines[prompt_end_idx + 1:stats_idx]
                corrected = "\n".join(generated_lines).strip()

        # Last resort fallback: clean the entire output using regex
        if not corrected:
            corrected = output.strip()
            corrected = re.sub(r"\[ Prompt:.*?\]", "", corrected, flags=re.DOTALL)
            corrected = re.sub(r"Exiting\.\.\.", "", corrected)
            corrected = re.sub(r"<\|im_(?:start|end)?\|>.*", "", corrected)
            corrected = corrected.strip()
        
        print(f"Corrected transcription: {corrected}")
        return corrected if corrected else raw_text
