import pytest
import numpy as np
import cv2
from pathlib import Path
import pickle

from src.detectors.bounding_box_detector import get_angular_detection
from src.io.frames import FrameData
from src.piano.key import AngularBounds
from src.io.camera_models import CameraIntrinsics

class TestBoundingBoxDetector:
    @pytest.fixture
    def mock_frame_data(self):
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
    def test_sequence(self):
        """Load test sequence for integration tests."""
        sequence_path = Path(__file__).parent.parent / "data" / "test_sequences" / "four_sectors.pkl"
        if not sequence_path.exists():
            pytest.skip("Test sequence not found. Run generate_test_data.py first.")
        
        with open(sequence_path, 'rb') as f:
            return pickle.load(f)

    @pytest.fixture
    def key_configs(self):
        """Provide test key configurations."""
        SECTOR_WIDTH = 86 / 9
        return {
            "far_left": AngularBounds(-43 + SECTOR_WIDTH, -43 + 2*SECTOR_WIDTH),   # Sector 1, Treble C4
            "left": AngularBounds(-43 + 3*SECTOR_WIDTH, -43 + 4*SECTOR_WIDTH),     # Sector 3, Bass C3
            "right": AngularBounds(-43 + 5*SECTOR_WIDTH, -43 + 6*SECTOR_WIDTH),    # Sector 5, Bass C3
            "far_right": AngularBounds(-43 + 7*SECTOR_WIDTH, -43 + 8*SECTOR_WIDTH) # Sector 7, Bass C2
        }

    def test_angular_detection_center(self, mock_frame_data):
        """Test detection of object in center sector."""
        bounds = AngularBounds(-10, 10)  # Center sector
        
        detection = get_angular_detection(mock_frame_data, bounds, "test", (255, 0, 0))
        
        assert detection is not None
        assert abs(detection.azimuth_deg) < 5  # Should be near center
        assert 0.9 < detection.min_distance_m < 1.1  # Should be around 1m

    @pytest.mark.parametrize("sector", ["far_left", "left", "right", "far_right"])
    def test_sequence_detection(self, test_sequence, sector, show_gui):
        """Test detection across a sequence of frames."""
        frame = test_sequence[0]
        frame_data = FrameData(
            color_image_rgb=frame.color_image,
            depth_image=frame.depth_image,
            depth_intrinsics=frame.intrinsics.to_realsense(),
            depth_scale=frame.depth_scale
        )
        
        # Calculate sector width (86° / 9)
        SECTOR_WIDTH = 86 / 9
        
        # Define sector bounds matching main.py configuration
        bounds_map = {
            "far_left": AngularBounds(-43 + SECTOR_WIDTH, -43 + 2*SECTOR_WIDTH),   # Sector 1
            "left": AngularBounds(-43 + 3*SECTOR_WIDTH, -43 + 4*SECTOR_WIDTH),     # Sector 3
            "right": AngularBounds(-43 + 5*SECTOR_WIDTH, -43 + 6*SECTOR_WIDTH),    # Sector 5
            "far_right": AngularBounds(-43 + 7*SECTOR_WIDTH, -43 + 8*SECTOR_WIDTH) # Sector 7
        }
        
        detection = get_angular_detection(frame_data, bounds_map[sector], sector, (255, 0, 0))
        
        if show_gui:
            cv2.imshow(f'{sector} Detection', frame_data.color_image_rgb)
            cv2.waitKey(1000)
            cv2.destroyAllWindows()
        
        assert detection is not None
        sector_center = (bounds_map[sector].min_azimuth + bounds_map[sector].max_azimuth) / 2
        assert bounds_map[sector].min_azimuth <= detection.azimuth_deg <= bounds_map[sector].max_azimuth, \
            f"Expected azimuth {detection.azimuth_deg}° to be within sector {sector} " \
            f"({bounds_map[sector].min_azimuth}° to {bounds_map[sector].max_azimuth}°)"

def test_note_generation():
    """Test note generation for different octaves and clefs."""
    treble_config = NoteConfig(octave=4, is_treble=True)
    bass_config = NoteConfig(octave=3, is_treble=False)
    
    # Test treble clef notes
    assert treble_config.get_note(0.3) == "C4"
    assert treble_config.get_note(4.0) == "C5"
    assert treble_config.get_note(2.15) == "G4"
    
    # Test bass clef notes
    assert bass_config.get_note(0.3) == "C3"
    assert bass_config.get_note(4.0) == "C4"
    assert bass_config.get_note(2.15) == "G3"
    
    # Test frequency generation
    assert abs(treble_config.get_frequency(0.3) - 261.63) < 0.1  # C4
    assert abs(bass_config.get_frequency(0.3) - 130.81) < 0.1    # C3

@pytest.mark.parametrize("sector,expected_octave", [
    ("far_left", 4),   # Treble clef
    ("left", 3),       # Bass clef
    ("right", 3),      # Bass clef
    ("far_right", 2)   # Bass clef
])
def test_sector_notes(key_configs, sector, expected_octave):
    """Test that each sector produces notes in the correct octave."""
    config = NoteConfig(
        octave=expected_octave,
        is_treble=(sector == "far_left")
    )
    
    # Test near distance
    note = config.get_note(0.5)
    assert note[0] in "CDEFGABC"
    assert int(note[-1]) == expected_octave