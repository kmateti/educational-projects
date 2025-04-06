from dataclasses import dataclass
import numpy as np
import pyrealsense2 as rs

@dataclass
class CameraIntrinsics:
    width: int
    height: int
    ppx: float  # Principal point X
    ppy: float  # Principal point Y
    fx: float   # Focal length X
    fy: float   # Focal length Y
    
    def to_realsense(self) -> rs.intrinsics:
        """Convert to RealSense intrinsics object."""
        intrinsics = rs.intrinsics()
        intrinsics.width = self.width
        intrinsics.height = self.height
        intrinsics.ppx = self.ppx
        intrinsics.ppy = self.ppy
        intrinsics.fx = self.fx
        intrinsics.fy = self.fy
        return intrinsics