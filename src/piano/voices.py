import math
from dataclasses import dataclass
from typing import Optional
import json
import yaml

# Add these constants at the top with other constants
# C major scale frequencies (C2 to C6)
C_MAJOR_FREQUENCIES = {
    # C2 to B2
    'C2': 65.41,
    'D2': 73.42,
    'E2': 82.41,
    'F2': 87.31,
    'G2': 98.00,
    'A2': 110.00,
    'B2': 123.47,
    
    # C3 to B3
    'C3': 130.81,
    'D3': 146.83,
    'E3': 164.81,
    'F3': 174.61,
    'G3': 196.00,
    'A3': 220.00,
    'B3': 246.94,
    
    # C4 to B4 (middle octave)
    'C4': 261.63,
    'D4': 293.66,
    'E4': 329.63,
    'F4': 349.23,
    'G4': 392.00,
    'A4': 440.00,
    'B4': 493.88,
    
    # C5 to B5
    'C5': 523.25,
    'D5': 587.33,
    'E5': 659.26,
    'F5': 698.46,
    'G5': 783.99,
    'A5': 880.00,
    'B5': 987.77,
    
    # C6
    'C6': 1046.50,

    # C7 to B7
    'C7': 2093.00,
    'D7': 2349.32,
    'E7': 2637.02,
    'F7': 2793.83,
    'G7': 3135.96,
    'A7': 3520.00,
    'B7': 3951.07,
    
    # C8
    'C8': 4186.01  # Highest note on a piano
}

# Middle C and one octave lower (C3 and C4)
C3_C4_FREQUENCIES = {
    note: C_MAJOR_FREQUENCIES[note]
    for note in ['C3', 'D3', 'E3', 'F3', 'G3', 'A3', 'B3', 'C4']
}

# C pentatonic scale (one octave)
C_PENTATONIC_FREQUENCIES = {
    note: C_MAJOR_FREQUENCIES[note]
    for note in ['C3', 'D3', 'E3', 'G3', 'A3','C4']
}

class DistanceToNoteMapper:
    def __init__(self, config_path: Optional[str] = None, min_range: float = 0.5, max_range: float = 3.5, lowest_note: str = 'A3', highest_note: str = 'C3'):
        self.min_range = min_range
        self.max_range = max_range
        self.lowest_note = lowest_note
        self.highest_note = highest_note
        self.ranges = []
        if config_path:
            self.load_config(config_path)
        
        self._calculate_ranges()

    def _calculate_ranges(self):
        """Calculate ranges for mapping distances to notes based on lowest and highest notes."""
        notes = list(C3_C4_FREQUENCIES.keys())
        start_index = notes.index(self.lowest_note)
        end_index = notes.index(self.highest_note) + 1
        selected_notes = notes[start_index:end_index]

        range_size = self.max_range - self.min_range
        section_size = range_size / len(selected_notes)
        self.ranges = [
            (self.max_range - (i + 1) * section_size, self.max_range - i * section_size, note)
            for i, note in enumerate(selected_notes)
        ]

    def load_config(self, config_path: str):
        """Load configuration from a YAML file."""
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)

        dist2note_config = config.get('distance_to_note_mapper')
        assert dist2note_config, "Configuration for distance_to_note_mapper not found."

        self.min_range = dist2note_config.get('min_range', 0.5)
        self.max_range = dist2note_config.get('max_range', 3.5)
        self.lowest_note = dist2note_config.get('lowest_note', 'A3')
        self.highest_note = dist2note_config.get('highest_note', 'C3')

    def save_config(self, config_path: str):
        """Save the current configuration to a JSON file."""
        config = {
            'min_range': self.min_range,
            'max_range': self.max_range,
            'lowest_note': self.lowest_note,
            'highest_note': self.highest_note,
        }
        with open(config_path, 'w') as file:
            json.dump(config, file, indent=4)

    def get_frequency_from_distance(self, min_distance_m: float) -> float:
        """Map distance to a note in C pentatonic scale with configurable range."""
        if min_distance_m < self.min_range or min_distance_m > self.max_range:
            return 0

        for min_sect, max_sect, note in self.ranges:
            if min_sect <= min_distance_m <= max_sect:
                return C3_C4_FREQUENCIES[note]

        return 0

    @staticmethod
    def get_note_from_frequency(frequency: float, tolerance: float = 1.0) -> str:
        """Map a frequency back to its note name."""
        for note, freq in C_MAJOR_FREQUENCIES.items():
            if abs(frequency - freq) / freq * 100 <= tolerance:
                return note
        return ""

    def get_note_from_distance(self, min_distance_m: float) -> str:
        """Map distance to a note in C major scale using logarithmic scaling."""
        frequency = self.get_frequency_from_distance(min_distance_m)
        return self.get_note_from_frequency(frequency)
