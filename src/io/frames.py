from dataclasses import dataclass
import numpy as np
import cv2
import pyrealsense2 as rs
from typing import Optional

@dataclass
class FrameData:
    color_image_rgb: np.ndarray
    depth_image: np.ndarray
    depth_intrinsics: rs.intrinsics
    depth_scale: float  # Added depth_scale fieldth_scale field

def get_color_and_depth_frames(pipeline: rs.pipeline, align: rs.align) -> Optional[FrameData]:
    """Get aligned color and depth frames from the RealSense camera."""

    frames = pipeline.wait_for_frames()
    aligned_frames = align.process(frames)
    
    depth_frame = aligned_frames.get_depth_frame()
    color_frame = aligned_frames.get_color_frame()

    if not depth_frame or not color_frame:
        return None

    # Get the depth sensor's depth scale
    depth_scale = pipeline.get_active_profile().get_device().first_depth_sensor().get_depth_scale()
    
    depth_intrinsics = depth_frame.profile.as_video_stream_profile().get_intrinsics()
        
    depth_image = np.asanyarray(depth_frame.get_data())
    color_image = np.asanyarray(color_frame.get_data())
    color_image_rgb = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)

    return FrameData(
        color_image_rgb=color_image_rgb,
        depth_image=depth_image,
        depth_intrinsics=depth_intrinsics,
        depth_scale=depth_scale
    )