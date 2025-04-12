from dataclasses import dataclass
from typing import Optional
import numpy as np

@dataclass
class AngularBounds:
    min_azimuth: float
    max_azimuth: float
    min_elevation: float = -5.0
    max_elevation: float = 5.0
    min_range: float = 0.3
    max_range: float = 4.0

@dataclass
class Channel:
    name: str
    color: tuple[int, int, int]
    angular_bounds: AngularBounds
    base_frequency: float  # Base frequency for this channel
    
    def get_frequency(self, distance_m: float) -> Optional[float]:
        """Convert distance to frequency."""
        if not (self.angular_bounds.min_range <= distance_m <= self.angular_bounds.max_range):
            return None
        return self.base_frequency