import time
import pyrealsense2 as rs
import numpy as np
from dataclasses import dataclass
import cv2
from typing import Optional

from src.io.frames import FrameData

MAX_RANGE_M = 3.5  # Maximum range for the bounding box in meters

@dataclass
class AngularBounds:
    """Defines an angular sector in camera space."""
    azimuth_center: float  # Degrees, 0 = center, negative = left, positive = right
    azimuth_span: float    # Degrees, total width of sector
    elevation_center: float = -10.0  # Degrees, 0 = center, negative = down, positive = up    
    elevation_span: float = 10.0  # Degrees, total height centered on 0
    min_range: float = 0.5  # Minimum detection distance in meters
    max_range: float = MAX_RANGE_M  # Maximum detection distance in meters

@dataclass
class SectorDetection:
    """Detection result for an angular sector."""
    min_distance_m: float
    num_valid_points: int
    azimuth_deg: float
    valid_mask: np.ndarray  # Mask of valid points in the sector

@dataclass
class Sector:
    """Represents a virtual piano sector in angular space."""
    name: str
    color: tuple[int, int, int]
    bounds: AngularBounds

    def detect(self, frame_data: FrameData) -> Optional[SectorDetection]:
        return get_angular_detection(frame_data, self.bounds, self.name, self.color)


def get_angular_detection(frame_data: FrameData, bounds: AngularBounds, name: str, color: tuple[int, int, int]) -> Optional[SectorDetection]:
    """Detect points within an angular sector."""
    height, width = frame_data.depth_image.shape
    depths = frame_data.depth_image.astype(float) / 1000.0  # Convert to meters

    # Create coordinate grid
    px, py = np.meshgrid(np.arange(width), np.arange(height))
    
    # Convert image coordinates to 3D rays using intrinsics
    fx = frame_data.depth_intrinsics.fx
    fy = frame_data.depth_intrinsics.fy
    ppx = frame_data.depth_intrinsics.ppx
    ppy = frame_data.depth_intrinsics.ppy
    
    x = (px - ppx) * depths / fx
    y = (py - ppy) * depths / fy
    z = depths
    
    # Calculate angles
    azimuth = np.rad2deg(np.arctan2(x, z))
    elevation = np.rad2deg(np.arctan2(y, z))
    
    # Create sector mask
    half_az_span = bounds.azimuth_span / 2
    half_el_span = bounds.elevation_span / 2
    
    valid_mask = (depths > bounds.min_range) & (depths < bounds.max_range) & \
                (azimuth >= bounds.azimuth_center - half_az_span) & \
                (azimuth <= bounds.azimuth_center + half_az_span) & \
                (elevation >= bounds.elevation_center - half_el_span) & \
                (elevation <= bounds.elevation_center + half_el_span)
    
    if not np.any(valid_mask):
        return None
    
    # Draw sector overlay
    depth_points = depths[valid_mask]
    min_distance = np.min(depth_points)
    
    # Visualize sector
    intensity = np.clip((1.0 - depth_points/bounds.max_range) * 255, 0, 255).astype(np.uint8)
    overlay = frame_data.color_image_rgb.copy()
    overlay[valid_mask] = tuple(int(c * 0.7) for c in color)  # Sector color at 70% intensity
    
    # Blend with original image
    alpha = 0.3
    frame_data.color_image_rgb[:] = cv2.addWeighted(
        frame_data.color_image_rgb, 1 - alpha,
        overlay, alpha, 0
    )
    
    return SectorDetection(
        min_distance_m=min_distance,
        num_valid_points=np.count_nonzero(valid_mask),
        azimuth_deg=bounds.azimuth_center,
        valid_mask=valid_mask
    )