import math
from dataclasses import dataclass
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

@dataclass
class RayConfig:
    azimuth_center: float
    azimuth_span: float
    elevation_center: float
    elevation_span: float

@dataclass
class NoteMapperConfig:
    min_range: float = 0.5
    max_range: float = 3.5
    lowest_note: str = 'C3'
    highest_note: str = 'C4'

@dataclass
class SectorConfig:
    name: str
    ray: RayConfig
    note_mapper: NoteMapperConfig

class SectorDistanceToNoteMapper:
    def __init__(self, note_mapper_config: NoteMapperConfig):
        self.min_range = note_mapper_config.min_range
        self.max_range = note_mapper_config.max_range
        self.lowest_note = note_mapper_config.lowest_note
        self.highest_note = note_mapper_config.highest_note
        self.ranges = []
        self._calculate_ranges()

    def _calculate_ranges(self):
        # Create a list of notes from the global C_MAJOR_FREQUENCIES dictionary.
        notes = list(C_MAJOR_FREQUENCIES.keys())
        start_index = notes.index(self.lowest_note)
        end_index = notes.index(self.highest_note) + 1
        selected_notes = notes[start_index:end_index]
        
        range_size = self.max_range - self.min_range
        section_size = range_size / len(selected_notes)
        self.ranges = [
            (self.max_range - (i + 1) * section_size, self.max_range - i * section_size, note)
            for i, note in enumerate(selected_notes)
        ]
        
    def get_note_from_distance(self, distance: float) -> str:
        """Return the note corresponding to the given distance."""
        for d_min, d_max, note in self.ranges:
            if d_min <= distance < d_max:
                return note
        # Return the last note if distance is beyond calculated range.
        return self.ranges[-1][2] if self.ranges else ""
    
    def get_frequency_from_distance(self, distance: float) -> float:
        """Return the frequency for the note corresponding to the given distance."""
        note = self.get_note_from_distance(distance)
        return C_MAJOR_FREQUENCIES.get(note, 0)
        
def load_sector_configs(config_path: str) -> dict[str, SectorConfig]:
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    
    sectors_list = config.get('sectors')
    if not sectors_list:
        raise ValueError("No sectors found in configuration.")

    sector_configs = {}
    for sec in sectors_list:
        ray_conf = RayConfig(
            azimuth_center=sec['angular']['azimuth_center'],  # still using 'angular' in config file
            azimuth_span=sec['angular']['azimuth_span'],
            elevation_center=sec['angular'].get('elevation_center', 0),
            elevation_span=sec['angular'].get('elevation_span', 0)
        )
        note_mapper_conf = NoteMapperConfig(
            min_range=sec['mapper'].get('min_range', 0.5),
            max_range=sec['mapper'].get('max_range', 3.5),
            lowest_note=sec['mapper'].get('lowest_note', 'C3'),
            highest_note=sec['mapper'].get('highest_note', 'C4')
        )
        sector_configs[sec['name']] = SectorConfig(
            name=sec['name'],
            ray=ray_conf,
            note_mapper=note_mapper_conf
        )
    return sector_configs
