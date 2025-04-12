import numpy as np
import pyaudio
import threading
from typing import List
from src.piano.notes import Note, get_frequency

class ToneGenerator:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.notes: List[Note] = []
        self.stream = None
        self.is_running = False
        self.pa = pyaudio.PyAudio()
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Generate audio samples."""
        if not self.notes:
            return (np.zeros(frame_count).astype(np.float32), pyaudio.paContinue)
        
        t = np.arange(frame_count) / self.sample_rate
        
        # Mix all active notes
        samples = np.zeros(frame_count)
        for note in self.notes:
            freq = get_frequency(note)
            samples += np.sin(2 * np.pi * freq * t)
        
        # Normalize
        if len(self.notes) > 0:
            samples = samples / len(self.notes)
            
        return (samples.astype(np.float32), pyaudio.paContinue)
    
    def start(self):
        """Start audio stream."""
        self.stream = self.pa.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=self.sample_rate,
            output=True,
            stream_callback=self.audio_callback,
            frames_per_buffer=1024
        )
        self.stream.start_stream()
        self.is_running = True
    
    def stop(self):
        """Stop audio stream."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.is_running = False
        self.pa.terminate()
    
    def set_notes(self, notes: List[Note]):
        """Update notes being played."""
        self.notes = notes