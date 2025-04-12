from enum import Enum
from typing import Dict

class Note(Enum):
    # Lower octave (Bass clef)
    C2 = "C2"
    D2 = "D2"
    E2 = "E2"
    F2 = "F2"
    G2 = "G2"
    A2 = "A2"
    B2 = "B2"
    
    # Middle octave
    C3 = "C3"
    D3 = "D3"
    E3 = "E3"
    F3 = "F3"
    G3 = "G3"
    A3 = "A3"
    B3 = "B3"
    
    # Higher octave (Treble clef)
    C4 = "C4"
    D4 = "D4"
    E4 = "E4"
    F4 = "F4"
    G4 = "G4"
    A4 = "A4"
    B4 = "B4"
    C5 = "C5"

def get_frequency(note: Note) -> float:
    """Convert musical note to frequency in Hz."""
    # Base frequencies for A4 = 440Hz
    BASE_A4_FREQ = 440.0
    
    # Semitones from A4 for each note in an octave
    SEMITONES = {
        'C': -9,
        'D': -7,
        'E': -5,
        'F': -4,
        'G': -2,
        'A': 0,
        'B': 2
    }
    
    note_name = note.value[0]  # Get note letter
    octave = int(note.value[1])  # Get octave number
    
    # Calculate semitones from A4
    semitones_from_a4 = SEMITONES[note_name] + (octave - 4) * 12
    
    # Calculate frequency using equal temperament formula
    return BASE_A4_FREQ * (2 ** (semitones_from_a4 / 12))