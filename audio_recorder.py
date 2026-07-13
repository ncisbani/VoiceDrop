import pyaudio
import wave
import threading
import os
import time
import numpy as np

class AudioRecorder:
    def __init__(self, device_index=None, sample_rate=16000, chunk_size=1024,
                 silence_callback=None, silence_threshold=500,
                 silence_duration=1.2):
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.format = pyaudio.paInt16
        self.channels = 1

        self.p = pyaudio.PyAudio()
        self.frames = []
        self.recording = False
        self.thread = None
        self.stream_error = None

        self.silence_callback = silence_callback
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration

    def _record_loop(self):
        try:
            stream = self.p.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size
            )
        except Exception as e:
            print(f"Error opening audio stream: {e}")
            self.recording = False
            self.stream_error = str(e)
            return

        voice_detected = False
        last_voice_time = None
        silence_fired = False

        while self.recording:
            try:
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                self.frames.append(data)

                if self.silence_callback and not silence_fired:
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2)) if len(audio_data) else 0.0
                    now = time.time()

                    if rms > self.silence_threshold:
                        voice_detected = True
                        last_voice_time = now
                    elif voice_detected and last_voice_time is not None:
                        if now - last_voice_time > self.silence_duration:
                            silence_fired = True
                            self.silence_callback()

            except Exception as e:
                print(f"Error reading audio data: {e}")
                break

        stream.stop_stream()
        stream.close()

    def start(self):
        if self.recording:
            return
        self.frames = []
        self.recording = True
        self.thread = threading.Thread(target=self._record_loop, daemon=True)
        self.thread.start()
        print("Audio recording started.")

    def stop(self, output_filepath):
        if not self.recording:
            return False

        self.recording = False
        if self.thread:
            self.thread.join()

        print("Audio recording stopped. Saving file...")
        try:
            os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
            wf = wave.open(output_filepath, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.p.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            print(f"Audio saved to {output_filepath}")
            return True
        except Exception as e:
            print(f"Error saving audio file: {e}")
            return False

    def cleanup(self):
        self.p.terminate()
