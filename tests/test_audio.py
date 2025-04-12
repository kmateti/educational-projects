import pytest
import numpy as np
from src.piano.key import get_frequency_from_distance
from src.piano.tone_generator import ToneGenerator
import time

def test_frequency_mapping():
    """Test that distances map to expected frequencies."""
    test_cases = [
        (0.5, "C5"),  # Close distance -> high note
        (2.0, "C4"),  # Middle distance -> middle C
        (3.5, "C3"),  # Far distance -> low note
    ]
    
    for distance, expected_note in test_cases:
        freq = get_frequency_from_distance(distance)
        assert freq > 0, f"Expected positive frequency for distance {distance}m"
        
        # Add expected frequencies for common notes
        if expected_note == "C4":
            assert abs(freq - 261.63) < 1, f"Expected middle C (261.63 Hz) for {distance}m, got {freq} Hz"

@pytest.mark.manual
def test_audio_output():
    """Test that we can generate and hear audio tones.
    
    This test requires human verification of the audio output.
    Run with: pytest tests/test_audio.py -v -m manual
    """
    tone_gen = ToneGenerator()
    tone_gen.start()
    
    try:
        # Test single frequency
        print("\nYou should hear a single tone (middle C)...")
        tone_gen.set_frequencies([261.63])  # Middle C
        time.sleep(2)
        
        # Test chord
        print("\nYou should hear a C major chord...")
        tone_gen.set_frequencies([261.63, 329.63, 392.00])  # C4, E4, G4
        time.sleep(2)
        
        # Test frequency sweep
        print("\nYou should hear ascending frequencies...")
        for freq in np.linspace(220, 880, 20):  # A3 to A5
            tone_gen.set_frequencies([freq])
            time.sleep(0.2)
            
    finally:
        tone_gen.stop()