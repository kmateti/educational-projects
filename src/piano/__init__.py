"""Piano package for RealSense musical instrument."""
from .key import Key, C_MAJOR_FREQUENCIES
from .tone_generator import ToneGenerator

__all__ = ['Key', 'C_MAJOR_FREQUENCIES', 'ToneGenerator']