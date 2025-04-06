import pyrealsense2 as rs
import numpy as np
import cv2
import time
from pathlib import Path

from src.config.camera_config import CameraConfig
from src.piano.key import Key, AngularBounds
from src.detectors.bounding_box_detector import get_angular_detection

def record_test_sequence(output_path: Path, config: CameraConfig, duration_sec: int = 10):
    """Record a test sequence with visual feedback."""
    
    # Initialize RealSense pipeline
    pipeline = rs.pipeline()
    cfg = rs.config()
    cfg.enable_stream(rs.stream.depth, config.width, config.height, 
                     rs.format.z16, config.fps)
    cfg.enable_stream(rs.stream.color, config.width, config.height, 
                     rs.format.rgb8, config.fps)
    
    # Start recording
    cfg.enable_record_to_file(str(output_path))
    pipeline.start(cfg)
    
    try:
        start_time = time.time()
        while time.time() - start_time < duration_sec:
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            
            if not color_frame:
                continue
                
            # Show preview
            color_image = np.asanyarray(color_frame.get_data())
            cv2.imshow('Recording Preview', color_image)
            
            if cv2.waitKey(1) == ord('q'):
                break
                
    finally:
        pipeline.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    config = CameraConfig()
    output_dir = Path(__file__).parent.parent / "data" / "test_recordings"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Stand in the center and move forward/backward to test distance detection")
    record_test_sequence(
        output_dir / "center_movement.bag",
        config,
        duration_sec=10
    )
    
    print("Move between the three sectors to test angular detection")
    record_test_sequence(
        output_dir / "angular_movement.bag",
        config,
        duration_sec=10
    )