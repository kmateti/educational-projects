import pytest
import numpy as np
import pyrealsense2 as rs
from pathlib import Path
import pickle

from src.detectors.bounding_box_detector import get_angular_detection
from src.io.frames import FrameData
from src.piano.key import AngularBounds
from src.io.camera_models import CameraIntrinsics

@pytest.fixture
def mock_frame_data():
    """Create synthetic frame data for testing."""
    width, height = 640, 480
    depth_image = np.zeros((height, width), dtype=np.uint16)
    
    # Create a synthetic depth pattern
    y, x = np.ogrid[:height, :width]
    center_y, center_x = height//2, width//2
    distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
    depth_image[distance < 100] = 1000  # 1m for central object
    
    # Create serializable intrinsics
    intrinsics = CameraIntrinsics(
        width=width,
        height=height,
        ppx=width // 2,
        ppy=height // 2,
        fx=500,
        fy=500
    )
    
    return FrameData(
        color_image_rgb=np.zeros((height, width, 3), dtype=np.uint8),
        depth_image=depth_image,
        depth_intrinsics=intrinsics.to_realsense(),
        depth_scale=0.001  # 1mm to meters
    )

@pytest.fixture
def test_sequence():
    """Load test sequence for integration tests."""
    sequence_path = Path(__file__).parent.parent / "data" / "test_sequences" / "three_sectors.pkl"
    if not sequence_path.exists():
        pytest.skip("Test sequence not found. Run generate_test_data.py first.")
    
    with open(sequence_path, 'rb') as f:
        return pickle.load(f)

def test_angular_detection_center(mock_frame_data):  # Add fixture as parameter
    """Test detection of object in center sector."""
    bounds = AngularBounds(-10, 10)  # Center sector
    
    detection = get_angular_detection(mock_frame_data, bounds, "test", (255, 0, 0))
    
    assert detection is not None
    assert abs(detection.azimuth_deg) < 5  # Should be near center
    assert 0.9 < detection.min_distance_m < 1.1  # Should be around 1m

@pytest.mark.parametrize("sector", ["left", "center", "right"])
def test_sequence_detection(test_sequence, sector, show_gui):
    """Test detection across a sequence of frames."""
    frame = test_sequence[0]
    frame_data = FrameData(
        color_image_rgb=frame.color_image,
        depth_image=frame.depth_image,
        depth_intrinsics=frame.intrinsics.to_realsense(),
        depth_scale=frame.depth_scale
    )
    
    # Define sector bounds
    bounds_map = {
        "left": AngularBounds(-30, -10),
        "center": AngularBounds(-10, 10),
        "right": AngularBounds(10, 30)
    }
    
    detection = get_angular_detection(frame_data, bounds_map[sector], sector, (255, 0, 0))
    
    if show_gui:
        cv2.imshow(f'{sector} Detection', frame_data.color_image_rgb)
        cv2.waitKey(1000)
        cv2.destroyAllWindows()
    
    assert detection is not None
    if sector == "left":
        assert detection.azimuth_deg < -10
    elif sector == "center":
        assert -10 <= detection.azimuth_deg <= 10
    else:
        assert detection.azimuth_deg > 10