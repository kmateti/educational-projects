from dataclasses import dataclass
import numpy as np
import cv2
import pyrealsense2 as rs

# Add this with the other imports at the top
@dataclass
class FrameData:
    color_image_rgb: np.ndarray
    depth_image: np.ndarray
    depth_colormap_image: np.ndarray
    depth_intrinsics: rs.intrinsics

# Then modify the get_color_and_depth_frames function:
def get_color_and_depth_frames(pipeline, align) -> FrameData:
    """Get aligned color and depth frames from the RealSense camera.
    
    Returns:
        FrameData: Contains color image (RGB), depth image, colored depth map, and depth intrinsics
    """
    frames = pipeline.wait_for_frames()
    aligned_frames = align.process(frames)
    aligned_depth_frame = aligned_frames.get_depth_frame()
    #depth_intrinsics = depth_frame.profile.as_video_stream_profile().intrinsics
    # Get intrinsics from aligned depth frame
    depth_intrinsics = aligned_depth_frame.profile.as_video_stream_profile().get_intrinsics()
    color_frame = aligned_frames.get_color_frame()

    if not aligned_depth_frame or not color_frame:
        return None

    color_image = np.asanyarray(color_frame.get_data())
    depth_image = np.asanyarray(aligned_depth_frame.get_data())

    depth_colormap = cv2.normalize(depth_image, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    depth_colormap_image = cv2.applyColorMap(depth_colormap, cv2.COLORMAP_JET)
    color_image_rgb = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
    
    return FrameData(
        color_image_rgb=color_image_rgb,
        depth_image=depth_image,
        depth_colormap_image=depth_colormap_image,
        depth_intrinsics=depth_intrinsics
    )