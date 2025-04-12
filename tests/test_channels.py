import pytest
import numpy as np
from dataclasses import dataclass
from src.piano.channel import Channel, AngularBounds
from src.piano.tone_generator import ToneGenerator
from src.piano.notes import Note
import time

def pytest_addoption(parser):
    parser.addoption(
        "--show-plot",
        action="store_true",
        default=False,
        help="Show test signal plots"
    )

@dataclass
class TimeSignal:
    """Represents a distance vs time signal for testing."""
    times: np.ndarray
    distances: np.ndarray

def create_test_signals(duration_sec: float = 10.0, fps: float = 30.0) -> list[TimeSignal]:
    """Create four test distance-time signals."""
    times = np.arange(0, duration_sec, 1/fps)
    
    signals = [
        # Channel 1: Sine wave
        TimeSignal(
            times=times,
            distances=2.0 + np.sin(2 * np.pi * 0.5 * times)
        ),
        # Channel 2: Square wave
        TimeSignal(
            times=times,
            distances=2.0 + 0.5 * np.sign(np.sin(2 * np.pi * 0.25 * times))
        ),
        # Channel 3: Sawtooth
        TimeSignal(
            times=times,
            distances=2.0 + 0.5 * (times % 2)
        ),
        # Channel 4: Random walk
        TimeSignal(
            times=times,
            distances=2.0 + np.cumsum(0.1 * np.random.randn(len(times)))
        )
    ]
    
    return signals

def create_mario_signals(duration_sec: float = 4.0, fps: float = 30.0) -> list[TimeSignal]:
    """Create Mario theme distance-time signals."""
    times = np.arange(0, duration_sec, 1/fps)
    
    # Mario first 7 notes: E5, E5, E5, C5, E5, G5, G4
    # Convert to distances (closer = higher pitch)
    note_timings = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]  # When each note starts
    note_distances = [0.5, 0.5, 0.5, 1.0, 0.5, 0.3, 2.0]  # Distance for each note
    
    # Create step function for distances
    distances = np.full_like(times, 4.0)  # Default to max distance
    for t, d in zip(note_timings, note_distances):
        mask = (times >= t) & (times < t + 0.4)  # Note duration
        distances[mask] = d
    
    # Only one channel plays the melody, others are silent (far distance)
    signals = [
        TimeSignal(times=times, distances=distances),  # Melody in first channel
        TimeSignal(times=times, distances=np.full_like(times, 4.0)),
        TimeSignal(times=times, distances=np.full_like(times, 4.0)),
        TimeSignal(times=times, distances=np.full_like(times, 4.0))
    ]
    
    return signals

@pytest.mark.parametrize("signal_creator", [create_test_signals, create_mario_signals])
def test_channel_response(signal_creator, request):
    """Test channels with synthetic distance signals."""
    
    # Create channels (using 86° FOV divided into 9 sectors)
    SECTOR_WIDTH = 86 / 9
    channels = [
        Channel("Melody", (0, 0, 255), 
                AngularBounds(-43 + SECTOR_WIDTH, -43 + 2*SECTOR_WIDTH),
                440.0),  # A4
        Channel("Bass", (0, 255, 0),
                AngularBounds(-43 + 3*SECTOR_WIDTH, -43 + 4*SECTOR_WIDTH),
                329.63), # E4
        Channel("Harmony", (255, 0, 0),
                AngularBounds(-43 + 5*SECTOR_WIDTH, -43 + 6*SECTOR_WIDTH),
                261.63), # C4
        Channel("Rhythm", (255, 0, 255),
                AngularBounds(-43 + 7*SECTOR_WIDTH, -43 + 8*SECTOR_WIDTH),
                196.00)  # G3
    ]
    
    # Generate test signals
    signals = signal_creator()
    
    # Test each channel's response
    for channel, signal in zip(channels, signals):
        frequencies = [channel.get_frequency(d) for d in signal.distances]
        assert all(f is not None for f in frequencies if 0.3 <= d <= 4.0)
        
        # if request.config.getoption("--show-plot"):
        #     plt.figure(figsize=(10, 4))
        #     plt.plot(signal.times, signal.distances)
        #     plt.title(f"{channel.name} Distance Signal")
        #     plt.xlabel("Time (s)")
        #     plt.ylabel("Distance (m)")
        #     plt.grid(True)
        #     plt.show()

@pytest.mark.manual
def test_audio_playback():
    """End-to-end test with audio output. Requires human verification."""
    signals = create_mario_signals()
    tone_gen = ToneGenerator()
    tone_gen.start()
    
    try:
        print("\nPlaying Mario theme through first channel...")
        start_time = time.time()
        
        for i in range(len(signals[0].times)):
            current_time = time.time() - start_time
            target_time = signals[0].times[i]
            
            # Wait until we reach the right time
            if current_time < target_time:
                time.sleep(target_time - current_time)
            
            # Get frequency for current distance
            freq = 440.0 * (4.0 - signals[0].distances[i]) / 3.7  # Scale distance to frequency
            tone_gen.set_frequencies([freq])
            
    finally:
        tone_gen.stop()

@pytest.mark.manual
def test_tone_quality():
    """Test simple tones using musical notes."""
    tone_gen = ToneGenerator()
    tone_gen.start()
    
    try:
        # Test single note
        print("\nPlaying middle C...")
        tone_gen.set_notes([Note.C4])
        time.sleep(1.0)
        
        # Test C major chord
        print("\nPlaying C major chord...")
        tone_gen.set_notes([Note.C4, Note.E4, Note.G4])
        time.sleep(1.0)
        
        # Test octave spread
        print("\nPlaying C across octaves...")
        tone_gen.set_notes([Note.C3, Note.C4, Note.C5])
        time.sleep(1.0)
        
    finally:
        tone_gen.stop()