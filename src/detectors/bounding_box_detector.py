import time
import pyrealsense2 as rs
import numpy as np
from dataclasses import dataclass
import cv2
from typing import Optional

from src.io.frames import FrameData
from src.piano.key import AngularBounds

MAX_RANGE_M = 4.0  # Maximum range for the bounding box in meters

@dataclass
class BoxDetection:
    """Represents a detection within a bounding box"""
    num_valid_points: int
    min_distance_m: float
    box_name: str

@dataclass
class SectorDetection:
    """Detection result for an angular sector."""
    min_distance_m: float
    num_valid_points: int
    azimuth_deg: float

def get_bounding_box_detections(frame_data: FrameData, bounds, name, color):
    """Get detections using aligned depth frame coordinates."""

    height, width = frame_data.depth_image.shape
    depths = frame_data.depth_image.astype(float) / 1000.0  # Convert to meters

    x_min, y_min, z_min = bounds[0]
    x_max, y_max, z_max = bounds[1]
    
    # Use camera intrinsics for proper projection
    fx = frame_data.depth_intrinsics.fx
    fy = frame_data.depth_intrinsics.fy
    ppx = frame_data.depth_intrinsics.ppx
    ppy = frame_data.depth_intrinsics.ppy
    
    corners_3d = [
        # Front face (z = z_min)
        (x_min, y_min, z_min),
        (x_max, y_min, z_min),
        (x_max, y_max, z_min),
        (x_min, y_max, z_min),
        # Back face (z = z_max)
        (x_min, y_min, z_max),
        (x_max, y_min, z_max),
        (x_max, y_max, z_max),
        (x_min, y_max, z_max),
    ]
    
    corners_2d = []
    for x, y, z in corners_3d:
        if z > 0:  # Avoid division by zero
            # Project using intrinsics
            pixel_x = int(x * fx / z + ppx)
            pixel_y = int(y * fy / z + ppy)
            if 0 <= pixel_x < width and 0 <= pixel_y < height:
                corners_2d.append((pixel_x, pixel_y))
                cv2.circle(frame_data.color_image_rgb, (pixel_x, pixel_y), 3, color, -1)
    
    # Draw box if we have enough corners
    if len(corners_2d) >= 4:
        # Draw front face
        for i in range(4):
            pt1 = corners_2d[i]
            pt2 = corners_2d[(i + 1) % 4]
            cv2.line(frame_data.color_image_rgb, pt1, pt2, color, 2)
        
        # Draw back face (if visible)
        if len(corners_2d) >= 8:
            for i in range(4):
                pt1 = corners_2d[i + 4]
                pt2 = corners_2d[((i + 1) % 4) + 4]
                cv2.line(frame_data.color_image_rgb, pt1, pt2, 
                        (color[0]//2, color[1]//2, color[2]//2), 1)
            
            # Draw connecting edges
            for i in range(4):
                pt1 = corners_2d[i]
                pt2 = corners_2d[i + 4]
                cv2.line(frame_data.color_image_rgb, pt1, pt2, color, 1)
    
    # Calculate points inside box
    px, py = np.meshgrid(np.arange(width), np.arange(height))
    valid_mask = (depths > 0) & \
                (px >= ppx + (x_min/z_min)*fx) & \
                (px <= ppx + (x_max/z_min)*fx) & \
                (py >= ppy + (y_min/z_min)*fy) & \
                (py <= ppy + (y_max/z_min)*fy) & \
                (depths >= z_min) & (depths <= z_max)
    
    min_distance_m = np.min(depths[valid_mask]) if np.any(valid_mask) else MAX_RANGE_M
    num_valid_points = np.count_nonzero(valid_mask)
    
    return BoxDetection(
        num_valid_points=num_valid_points,
        min_distance_m=min_distance_m,
        box_name=name
    ), frame_data.color_image_rgb

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
                (elevation >= -half_el_span) & \
                (elevation <= half_el_span)
    
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
        azimuth_deg=bounds.azimuth_center
    )