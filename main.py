import sys
import os
import socket
import subprocess
import threading
import tempfile
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

import config
from audio_recorder import AudioRecorder
from transcriber import Transcriber
from paster import paste_text
from overlay import OverlayWindow
from settings_gui import SettingsWindow

SOCKET_PATH = "/tmp/voicedrop.sock"

class VoiceDropDaemon:
    def __init__(self):
        self.cfg = config.load_config()
        self.recorder = None
        self.transcriber = None
        self.overlay = None
        self.server_socket = None
        self.running = False
        self.temp_wav = None
        
        # Paths
        base_dir = "/home/ncisbani/Documents/varie/VoiceDrop"
        whisper_cli = os.path.join(base_dir, "whisper.cpp/build/bin/whisper-cli")
        llama_cli = os.path.join(base_dir, "llama.cpp/build/bin/llama-cli")
        
        self.transcriber = Transcriber(
            whisper_cli_path=whisper_cli,
            whisper_model=self.cfg.get("whisper_model"),
            llama_cli_path=llama_cli,
            llm_model=self.cfg.get("llm_model")
        )

    def get_mic_volume(self):
        """Callback for the overlay visualizer to read mic volume."""
        if self.recorder and self.recorder.frames:
            try:
                import numpy as np
                last_frame = self.recorder.frames[-1]
                audio_data = np.frombuffer(last_frame, dtype=np.int16)
                if len(audio_data) > 0:
                    rms = np.sqrt(np.mean(audio_data.astype(np.float32)**2))
                    return rms / 32768.0 # Normalize 0 to 1
            except Exception:
                pass
        return 0.05

    def on_silence_detected(self):
        # fires from recorder's background thread, must marshal into GTK main loop
        GLib.idle_add(self.stop_recording_from_gui)

    def start(self):
        self.running = True
        
        # 1. Create temp WAV path
        self.temp_wav = os.path.join(tempfile.gettempdir(), "voicedrop_recording.wav")
        if os.path.exists(self.temp_wav):
            try:
                os.remove(self.temp_wav)
            except Exception:
                pass

        # 2. Start audio recorder
        self.recorder = AudioRecorder(
            device_index=self.cfg.get("audio_device_index"),
            silence_callback=self.on_silence_detected
        )
        self.recorder.start()

        # 3. Open GTK Overlay window
        self.overlay = OverlayWindow(
            stop_callback=self.stop_recording_from_gui,
            get_volume_callback=self.get_mic_volume
        )
        self.overlay.set_state("listening")
        self.overlay.show_all()

        # 4. Start Unix Socket Server to listen for toggle signals
        self.start_socket_server()
        
        # Run GTK Main Loop
        Gtk.main()

    def start_socket_server(self):
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)
            
        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.bind(SOCKET_PATH)
        self.server_socket.listen(1)
        
        def socket_thread_func():
            print("Daemon socket server listening...")
            while self.running:
                try:
                    self.server_socket.settimeout(1.0)
                    conn, _ = self.server_socket.accept()
                    data = conn.recv(1024).decode('utf-8')
                    if "toggle" in data:
                        print("Toggle signal received via socket.")
                        # Thread-safe stop trigger in GTK main thread
                        GLib.idle_add(self.stop_recording_from_gui)
                        conn.sendall(b"OK")
                    conn.close()
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Socket server error: {e}")
                    break
                    
        t = threading.Thread(target=socket_thread_func, daemon=True)
        t.start()

    def stop_recording_from_gui(self):
        """Stops the recording, switches UI to processing, and starts transcription."""
        if not self.running:
            return False
            
        self.running = False
        self.overlay.set_state("processing")
        
        # Stop recording in a background thread so we don't freeze the GTK UI
        def process_audio_thread():
            # 1. Stop audio recorder and save WAV
            self.recorder.stop(self.temp_wav)
            self.recorder.cleanup()
            
            text = ""
            try:
                # 2. Transcribe WAV file
                raw_text = self.transcriber.transcribe(self.temp_wav, language=self.cfg.get("language", "en"))
                
                # 3. Apply LLM Correction if enabled
                if self.cfg.get("llm_correction", True):
                    text = self.transcriber.correct_text(raw_text, language=self.cfg.get("language", "en"))
                else:
                    text = raw_text
            except Exception as e:
                print(f"Transcription failed: {e}")
                # Fallback: simple notification
                try:
                    subprocess.run(["notify-send", "VoiceDrop Error", str(e)])
                except Exception:
                    pass
            
            # Clean up temporary audio file
            if os.path.exists(self.temp_wav):
                try:
                    os.remove(self.temp_wav)
                except Exception:
                    pass
                    
            # 4. Copy and paste text
            if text.strip():
                import time
                if self.overlay:
                    GLib.idle_add(self.overlay.hide)
                time.sleep(0.2)  # Wait for focus to return to original window
                
                if self.cfg.get("auto_paste", True):
                    paste_text(text)
                else:
                    from paster import copy_to_clipboard
                    copy_to_clipboard(text)
                    try:
                        subprocess.run([
                            "notify-send", 
                            "VoiceDrop", 
                            "Text copied to clipboard! Press Ctrl+V to paste.", 
                            "-i", "accessories-character-map", 
                            "-t", "4000"
                        ])
                    except Exception:
                        pass
                
            # Close UI in GTK main thread
            GLib.idle_add(self.cleanup_and_quit)
            
        t = threading.Thread(target=process_audio_thread, daemon=True)
        t.start()
        return False

    def cleanup_and_quit(self):
        # Stop socket server
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
            if os.path.exists(SOCKET_PATH):
                os.remove(SOCKET_PATH)
                
        # Close GTK Window
        if self.overlay:
            self.overlay.close_window()
        else:
            Gtk.main_quit()

def toggle_recording():
    """Tries to connect to running daemon. If found, sends toggle signal. If not, spawns daemon."""
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(2.0) # Prevent hanging forever if daemon is deadlocked
        client.connect(SOCKET_PATH)
        client.sendall(b"toggle")
        client.recv(1024)
        client.close()
        print("Sent toggle command to active VoiceDrop daemon.")
    except (socket.error, socket.timeout, FileNotFoundError) as e:
        print(f"No active or responsive daemon found ({type(e).__name__}). Cleaning up and spawning daemon...")
        if os.path.exists(SOCKET_PATH):
            try:
                os.remove(SOCKET_PATH)
            except Exception:
                pass
        daemon = VoiceDropDaemon()
        daemon.start()

def main():
    if "--toggle" in sys.argv:
        toggle_recording()
    else:
        # Open Settings window
        app = SettingsWindow()
        Gtk.main()

if __name__ == "__main__":
    main()
