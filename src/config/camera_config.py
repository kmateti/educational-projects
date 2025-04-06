from dataclasses import dataclass

@dataclass
class CameraConfig:
    width: int = 1280
    height: int = 720
    fps: int = 30
    enable_color: bool = True
    enable_depth: bool = True
    depth_format: str = 'Z16'
    color_format: str = 'RGB8'
    filter_magnitude: int = 2  # Temporal filter strength