import numpy as np
import pyaudio
from typing import List

class ToneGenerator:
    def __init__(self, sample_rate=44100, buffer_size=1024):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.stream = None
        self.audio = pyaudio.PyAudio()
        self.current_frequencies = [0.0, 0.0, 0.0, 0.0]  # Support for 4 channels
        self.target_frequencies = [0.0, 0.0, 0.0, 0.0]
        self.is_running = False
        self.phase = [0.0, 0.0, 0.0, 0.0]  # Keep track of phase for continuity
        self.sample_positions = np.arange(self.buffer_size, dtype=np.float32) / self.sample_rate
        
        # Frequency smoothing parameters
        self.smoothing_factor = 0.05
        
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Generate continuous audio samples with phase continuity."""
        if not self.is_running:
            return (np.zeros(frame_count, dtype=np.float32), pyaudio.paComplete)
        
        # Smooth frequency transitions
        for i in range(len(self.current_frequencies)):
            self.current_frequencies[i] = (self.smoothing_factor * self.current_frequencies[i] + 
                                         (1 - self.smoothing_factor) * self.target_frequencies[i])
        
        # Generate samples
        t = self.sample_positions[:frame_count]
        samples = np.zeros(frame_count, dtype=np.float32)
        
        for i, freq in enumerate(self.current_frequencies):
            if freq > 0:
                # Continue phase from previous buffer
                phase = 2 * np.pi * freq * t + self.phase[i]
                samples += 0.25 * np.sin(phase)  # Reduced amplitude for mixing
                # Store ending phase for next buffer
                self.phase[i] = phase[-1] % (2 * np.pi)
        
        return (samples.astype(np.float32), pyaudio.paContinue)
    
    def start(self):
        """Start audio stream in separate thread."""
        if self.is_running:
            return
            
        self.is_running = True
        self.stream = self.audio.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=self.sample_rate,
            output=True,
            frames_per_buffer=self.buffer_size,
            stream_callback=self.audio_callback
        )
        self.stream.start_stream()
    
    def stop(self):
        """Stop audio stream."""
        self.is_running = False
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()
    
    def set_frequencies(self, frequencies: List[float]):
        """Update target frequencies for up to four simultaneous voices."""
        freqs = list(frequencies) + [0.0] * (4 - len(frequencies))
        self.target_frequencies = freqs[:4]