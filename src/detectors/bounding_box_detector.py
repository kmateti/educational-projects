import time
import pyrealsense2 as rs
import numpy as np
from dataclasses import dataclass
import cv2

from src.io.frames import FrameData

MAX_RANGE_M = 4.0  # Maximum range for the bounding box in meters

@dataclass
class BoxDetection:
    """Represents a detection within a bounding box"""
    num_valid_points: int
    min_distance_m: float
    box_name: str

def get_bounding_box_detections(frame_data: FrameData, bounds, name, color):
    tic = time.time()
    height, width  = frame_data.depth_image.shape
    px, py = np.meshgrid(np.arange(width), np.arange(height))
    depths = frame_data.depth_image.astype(float) / 1000.0  # Convert to meters

    x_min, y_min, z_min = bounds[0]
    x_max, y_max, z_max = bounds[1]
        
    # Project 3D corners to 2D image space
    corners_3d = [
        (x_min, y_min, z_min),  # Front bottom left
        (x_max, y_min, z_min),  # Front bottom right
        (x_max, y_max, z_min),  # Front top right
        (x_min, y_max, z_min),  # Front top left
    ]
    
    corners_2d = []
    for x, y, z in corners_3d:
        pixel = rs.rs2_project_point_to_pixel(frame_data.depth_intrinsics, [x, y, z])
        corners_2d.append((int(pixel[0]), int(pixel[1])))
    projection_time = time.time() - tic
    # Draw box
    for i in range(len(corners_2d)):
        pt1 = corners_2d[i]
        pt2 = corners_2d[(i + 1) % len(corners_2d)]
        cv2.line(frame_data.color_image_rgb, pt1, pt2, color, 2)
    
    # Calculate points and distance inside box
    X = (px - frame_data.depth_intrinsics.ppx) * depths / frame_data.depth_intrinsics.fx
    Y = (py - frame_data.depth_intrinsics.ppy) * depths / frame_data.depth_intrinsics.fy
    Z = depths
    
    valid_mask = (depths > 0) & (X >= x_min) & (X <= x_max) & \
                (Y >= y_min) & (Y <= y_max) & \
                (Z >= z_min) & (Z <= z_max)
    
    min_distance_m = np.min(depths[valid_mask]) if np.any(valid_mask) else MAX_RANGE_M
    num_valid_points = np.count_nonzero(valid_mask)
    
    detection = BoxDetection(
        num_valid_points=num_valid_points,
        min_distance_m=min_distance_m,
        box_name=name
    )

    detection_time = time.time() - projection_time
    #print(f"{projection_time=}, {detection_time=}")
    return detection