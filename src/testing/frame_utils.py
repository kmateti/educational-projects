from dataclasses import dataclass
import numpy as np
from src.io.camera_models import CameraIntrinsics

@dataclass
class SimulatedFrame:
    depth_image: np.ndarray
    color_image: np.ndarray
    intrinsics: CameraIntrinsics
    depth_scale: float
    timestamp: float