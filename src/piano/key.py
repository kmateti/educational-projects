import math
from dataclasses import dataclass
from typing import Optional


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


def get_frequency_from_distance(min_distance_m):
    """Map distance to a note in C major scale using logarithmic scaling."""
    # Normalize distance to 0-1 range using log scale
    # Add small epsilon to avoid log(0)
    epsilon = 0.001
    log_min = math.log(epsilon)
    log_max = math.log(MAX_RANGE_M + epsilon)
    
    # Calculate normalized position in log space
    log_dist = math.log(min_distance_m + epsilon)
    normalized_dist = (log_dist - log_min) / (log_max - log_min)
    normalized_dist = max(0, min(1, normalized_dist))
    
    # Map to index in C major scale
    notes = list(C_MAJOR_FREQUENCIES.values())[::-1]  # Reverse for descending scale
    index = int(normalized_dist * (len(notes) - 1))
    
    # Return the frequency
    return notes[index]

@dataclass
class AngularBounds:
    min_azimuth: float  # degrees, negative is left of center
    max_azimuth: float  # degrees
    min_elevation: float = -5.0  # degrees, fixed small range
    max_elevation: float = 5.0   # degrees
    min_range: float = 0.3       # meters
    max_range: float = 4.0       # meters

@dataclass
class Key:
    """Represents a virtual piano key in 3D space."""
    name: str
    color: tuple[int, int, int]
    angular_bounds: AngularBounds
    
    def get_frequency(self, distance: float, valid_points: int) -> float:
        """Calculate frequency based on the minimum distance if enough valid points."""
        return get_frequency_from_distance(distance) if valid_points > 10 else 0
    
    def get_note(self, distance_m: float) -> Optional[str]:
        """Convert distance to musical note."""
        if not self.angular_bounds.min_range <= distance_m <= self.angular_bounds.max_range:
            return None
            
        if distance_m < 1.0:
            return "C4"
        elif distance_m < 2.0:
            return "E4"
        elif distance_m < 3.0:
            return "G4"
        else:
            return "C5"