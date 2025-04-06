"""io Input/Output package for RealSense frames."""
from .frames import FrameData, get_color_and_depth_frames

__all__ = ['FrameData', 'get_color_and_depth_frames']