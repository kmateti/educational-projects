import math
from dataclasses import dataclass


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

MAX_RANGE_M = 4.0  # Maximum range for the bounding box in meters

def get_note_from_distance(min_distance_m):
    """Map distance to a note in C major scale using logarithmic scaling."""
    # Return the note name
    return get_note_from_frequency(get_frequency_from_distance(min_distance_m))

# def get_frequency_from_distance(avg_distance_m):
#     """Calculate frequency based on average distance."""
#     # Example: Frequency decreases as distance increases
#     # This is a simple linear mapping; adjust as needed
#     return int(50 + 1000 * max(MAX_RANGE_M - avg_distance_m, 0))  # Adjust the scaling factor as needed
def get_note_from_frequency(frequency: float, tolerance: float = 1.0) -> str:
    """Map a frequency back to its note name.
    Args:
        frequency: The frequency to map
        tolerance: How close the frequency needs to be to match (percentage)
    Returns:
        The note name or empty string if no match found
    """
    for note, freq in C_MAJOR_FREQUENCIES.items():
        # Check if frequency is within tolerance % of the target frequency
        if abs(frequency - freq) / freq * 100 <= tolerance:
            return note
    return ""


# C pentatonic scale (one octave)
C_PENTATONIC_FREQUENCIES = {
    note: C_MAJOR_FREQUENCIES[note]
    for note in ['C3', 'D3', 'E3', 'G3', 'A3','C4']
}

# Calculate section size for 5 notes
min_range = 0.5  # Minimum operating distance (closest = highest note)
max_range = 3.5  # Maximum operating distance (furthest = lowest note)
range_size = max_range - min_range
section_size = range_size / 5

# Map distance ranges to notes (closer = higher pitch)
ranges = [
    (max_range - section_size, max_range, 'C3'),      # Furthest = lowest note
    (max_range - 2*section_size, max_range - section_size, 'D3'),
    (max_range - 3*section_size, max_range - 2*section_size, 'E3'),
    (max_range - 4*section_size, max_range - 3*section_size, 'G3'),
    (min_range, max_range - 4*section_size, 'A3')     # Closest = highest note
]

def get_frequency_from_distance(min_distance_m: float, 
                              min_range: float = 0.5, 
                              max_range: float = 3.5) -> float:
    """Map distance to a note in C pentatonic scale with configurable range.
    
    Args:
        min_distance_m: Distance in meters
        min_range: Minimum operating distance (closest = highest note)
        max_range: Maximum operating distance (furthest = lowest note)
        
    Returns:
        float: Frequency of the corresponding note
    """
    if min_distance_m < min_range or min_distance_m > max_range:
        return 0
    
    # Find which range the distance falls into
    for min_sect, max_sect, note in ranges:
        if min_sect <= min_distance_m <= max_sect:
            return C_PENTATONIC_FREQUENCIES[note]
    
    return 0

@dataclass
class Key:
    """Represents a virtual piano key in 3D space."""
    name: str
    color: tuple[int, int, int]
    bounds: tuple[tuple[float, float, float], tuple[float, float, float]]  # ((min_x, min_y, min_z), (max_x, max_y, max_z))
    
    def get_frequency(self, distance: float, valid_points: int) -> float:
        """Calculate frequency based on the minimum distance if enough valid points."""
        return get_frequency_from_distance(distance) if valid_points > 10 else 0
    
    def get_note(self, distance: float, valid_points: int) -> str:
        """Get the musical note name based on the distance if enough valid points."""
        freq = self.get_frequency(distance, valid_points)
        return get_note_from_frequency(freq) if freq > 0 else ""