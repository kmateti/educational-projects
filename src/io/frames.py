from dataclasses import dataclass
import numpy as np
import pyrealsense2 as rs
from typing import Optional

@dataclass
class FrameData:
    color_image: np.ndarray
    depth_image: np.ndarray
    depth_intrinsics: rs.intrinsics

def get_color_and_depth_frames(pipeline, align) -> Optional[FrameData]:
    """Get aligned color and depth frames from the RealSense camera.
    
    Returns:
        FrameData: Contains color image, depth image, and depth intrinsics.
    """
    frames = pipeline.wait_for_frames()
    aligned_frames = align.process(frames)
    aligned_depth_frame = aligned_frames.get_depth_frame()
    color_frame = aligned_frames.get_color_frame()

    if not aligned_depth_frame or not color_frame:
        return None

    depth_intrinsics = aligned_depth_frame.profile.as_video_stream_profile().get_intrinsics()

    color_image = np.asanyarray(color_frame.get_data())
    depth_image = np.asanyarray(aligned_depth_frame.get_data())
    
    return FrameData(
        color_image=color_image,
        depth_image=depth_image,
        depth_intrinsics=depth_intrinsics
    )