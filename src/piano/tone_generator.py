import numpy as np
import pyaudio
import threading
from queue import Queue
from typing import Optional, List

SAMPLE_RATE = 44100
CHUNK_SIZE = 1024
FORMAT = pyaudio.paFloat32

class ToneGenerator:
    def __init__(self):
        self.stream: Optional[pyaudio.Stream] = None
        self.p: Optional[pyaudio.PyAudio] = None
        self.num_frequencies: int = 3  # Number of frequencies to mix
        self.frequencies: List[float] = [0, 0, 0]  # Three frequencies
        self.running = False
        self.freq_queue = Queue()

    def _generate_chunk(self) -> np.ndarray:
        samples = np.arange(CHUNK_SIZE)
        # Mix three sine waves with different amplitudes
        tone = np.zeros(CHUNK_SIZE)
        for i, freq in enumerate(self.frequencies):
            if freq > 0:
                # Decrease amplitude for each additional frequency to prevent clipping
                amplitude = (1.0 / self.num_frequencies) / (i + 1)
                tone += amplitude * np.sin(2 * np.pi * freq * samples / SAMPLE_RATE)
        return tone.astype(np.float32)

    def _audio_thread(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=FORMAT,
            channels=1,
            rate=SAMPLE_RATE,
            output=True,
            frames_per_buffer=CHUNK_SIZE
        )

        while self.running:
            # Update frequencies if new values available
            while not self.freq_queue.empty():
                self.frequencies = self.freq_queue.get()
            
            if any(f > 0 for f in self.frequencies):
                chunk = self._generate_chunk()
                self.stream.write(chunk.tobytes())

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.p:
            self.p.terminate()

    def start(self):
        self.running = True
        threading.Thread(target=self._audio_thread, daemon=True).start()

    def stop(self):
        self.running = False
        self.frequencies = [0, 0, 0]

    def set_frequencies(self, freqs: List[float]):
        """Set up to three frequencies to play simultaneously"""
        self.freq_queue.put(freqs[:self.num_frequencies])  # Limit to three frequencies