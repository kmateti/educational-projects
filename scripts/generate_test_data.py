import numpy as np
import cv2
from pathlib import Path
import pickle

from src.testing.frame_utils import SimulatedFrame
from src.io.camera_models import CameraIntrinsics

def create_synthetic_scene(width: int = 640, height: int = 480, frame_idx: int = 0):
    """Create synthetic depth and color images with moving objects."""
    
    # Create empty depth image (4000mm = 4.0m background)
    depth_image = np.full((height, width), 4000, dtype=np.uint16)
    color_image = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Create three vertical sectors
    sector_width = width // 3
    
    # Animate objects in each sector based on frame index
    t = frame_idx / 30.0  # Assuming 30fps
    for i in range(3):
        # Oscillating distance between 0.5m and 3.5m
        distance = 2000 + 1500 * np.sin(t + i * 2 * np.pi / 3)  # in mm
        
        # Create object in sector
        x_center = (i + 0.5) * sector_width
        y_center = height // 2
        
        # Create circular object
        y, x = np.ogrid[:height, :width]
        mask = ((x - x_center) ** 2 + (y - y_center) ** 2) < 1000
        depth_image[mask] = distance
        
        # Add color
        colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0)]
        color_image[mask] = colors[i]
    
    intrinsics = CameraIntrinsics(
        width=width,
        height=height,
        ppx=width // 2,
        ppy=height // 2,
        fx=500,
        fy=500
    )
    
    return SimulatedFrame(
        depth_image=depth_image,
        color_image=color_image,
        intrinsics=intrinsics,
        depth_scale=0.001,
        timestamp=frame_idx / 30.0
    )

def generate_test_sequence(output_path: Path, num_frames: int = 300, show_gui: bool = False):
    """Generate a test sequence and save to file."""
    frames = []
    
    for i in range(num_frames):
        frame = create_synthetic_scene(frame_idx=i)
        frames.append(frame)
        
        if show_gui:
            # Visualize while generating
            normalized = cv2.normalize(frame.depth_image, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            depth_colormap = cv2.applyColorMap(normalized, cv2.COLORMAP_JET)
            cv2.imshow('Depth Preview', depth_colormap)
            if cv2.waitKey(1) == ord('q'):
                break
    
    # Save sequence
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'wb') as f:
        pickle.dump(frames, f)
    
    if show_gui:
        cv2.destroyAllWindows()
    print(f"Generated {len(frames)} frames, saved to {output_path}")

if __name__ == "__main__":
    output_dir = Path(__file__).parent.parent / "data" / "test_sequences"
    generate_test_sequence(output_dir / "three_sectors.pkl")