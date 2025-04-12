import time
import pyrealsense2 as rs
import numpy as np
from dataclasses import dataclass
import cv2
from math import degrees, atan2, sqrt
from typing import Optional

from src.io.frames import FrameData

MAX_RANGE_M = 4.0  # Maximum range for the bounding box in meters

@dataclass
class Detection:
    min_distance_m: float
    num_valid_points: int
    azimuth_deg: float
    sector_points: list[tuple[int, int]]  # List of (x,y) points defining sector

def get_bounding_box_detections(
    frame_data: 'FrameData',
    bounds: tuple[tuple[float, float, float], tuple[float, float, float]],
    name: str,
    color: tuple[int, int, int]
) -> Detection | None:
    """Get distance measurements within a 3D bounding box."""
    
    # Convert 3D bounds to 2D screen coordinates
    box_points = []
    for point in [
        (bounds[0][0], bounds[0][1], bounds[0][2]),  # Near corner
        (bounds[1][0], bounds[1][1], bounds[1][2])   # Far corner
    ]:
        pixel = rs.rs2_project_point_to_pixel(
            frame_data.depth_intrinsics, 
            [point[0], point[1], point[2]]
        )
        box_points.append((int(pixel[0]), int(pixel[1])))

    # Draw the 2D bounding box
    cv2.rectangle(
        frame_data.color_image_rgb,
        box_points[0],
        box_points[1],
        color,
        2
    )

    # Get depth values within the box
    x1, y1 = box_points[0]
    x2, y2 = box_points[1]
    x1, x2 = min(x1, x2), max(x1, x2)
    y1, y2 = min(y1, y2), max(y1, y2)
    
    depth_roi = frame_data.depth_image[y1:y2, x1:x2]
    
    # Filter out zero depth values
    valid_depths = depth_roi[depth_roi > 0]
    
    if len(valid_depths) == 0:
        return None

    return Detection(
        min_distance_m=np.min(valid_depths) / 1000.0,  # Convert mm to meters
        num_valid_points=len(valid_depths),
        azimuth_deg=0.0,  # Placeholder value
        sector_points=[(x1, y1), (x2, y2)]
    )

def get_angular_detection(
    frame_data: FrameData,
    bounds: AngularBounds,
    name: str,
    color: tuple[int, int, int]
) -> Optional[Detection]:
    """Get distance measurements within an angular sector."""
    
    height, width = frame_data.depth_image.shape
    depth_scale = frame_data.depth_scale
    
    # Create pixel coordinates
    pixel_x, pixel_y = np.meshgrid(np.arange(width), np.arange(height))
    
    # Get camera parameters
    fx = frame_data.depth_intrinsics.fx
    fy = frame_data.depth_intrinsics.fy
    ppx = frame_data.depth_intrinsics.ppx
    ppy = frame_data.depth_intrinsics.ppy
    
    # Convert depth to meters
    depth = frame_data.depth_image * depth_scale
    
    # Vectorized deprojection using camera model equations
    x_coords = (pixel_x - ppx) * depth / fx
    y_coords = (pixel_y - ppy) * depth / fy
    z_coords = depth
    
    # Calculate angles
    azimuth = np.degrees(np.arctan2(x_coords, z_coords))
    elevation = np.degrees(np.arctan2(y_coords, z_coords))
    ranges = np.sqrt(x_coords**2 + y_coords**2 + z_coords**2)
    
    # Create mask for points within angular bounds
    mask = (
        (azimuth >= bounds.min_azimuth) & 
        (azimuth <= bounds.max_azimuth) &
        (elevation >= bounds.min_elevation) &
        (elevation <= bounds.max_elevation) &
        (ranges >= bounds.min_range) &
        (ranges <= bounds.max_range) &
        (depth > 0)  # Only consider valid depth points
    )
    
    valid_depths = frame_data.depth_image[mask]
    if len(valid_depths) == 0:
        return None
        
    # Draw the sector boundaries
    sector_points = []
    for az in [bounds.min_azimuth, bounds.max_azimuth]:
        for r in [bounds.min_range, bounds.max_range]:
            x = r * np.sin(np.radians(az))
            z = r * np.cos(np.radians(az))
            pixel = rs.rs2_project_point_to_pixel(
                frame_data.depth_intrinsics,
                [x, 0, z]
            )
            sector_points.append((int(pixel[0]), int(pixel[1])))
    
    # Draw the sector
    cv2.polylines(
        frame_data.color_image_rgb,
        [np.array(sector_points)],
        True,
        color,
        2
    )
    
    return Detection(
        min_distance_m=np.min(valid_depths) / 1000.0,
        num_valid_points=len(valid_depths),
        azimuth_deg=np.mean(azimuth[mask]),
        sector_points=sector_points
    )