import numpy as np
import cv2
from pathlib import Path
import pickle

from src.testing.frame_utils import SimulatedFrame
from src.io.camera_models import CameraIntrinsics

def create_synthetic_scene(width: int = 640, height: int = 480, frame_idx: int = 0):
    """Create synthetic depth and color images with four moving objects."""
    
    # Create empty depth image (4000mm = 4.0m background)
    depth_image = np.full((height, width), 4000, dtype=np.uint16)
    color_image = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Calculate sector positions (9 sectors, use sectors 1,3,5,7)
    sector_width = width // 9
    key_sectors = [1, 3, 5, 7]  # Sectors for the four keys
    
    # Animate objects in each key sector based on frame index
    t = frame_idx / 30.0  # Assuming 30fps
    for i, sector in enumerate(key_sectors):
        # Oscillating distance between 0.5m and 3.5m
        distance = 2000 + 1500 * np.sin(t + i * np.pi / 2)  # in mm
        
        # Create object in sector
        x_center = (sector + 0.5) * sector_width
        y_center = height // 2
        
        # Create circular object
        y, x = np.ogrid[:height, :width]
        mask = ((x - x_center) ** 2 + (y - y_center) ** 2) < 800
        depth_image[mask] = distance
        
        # Add color (BGR format)
        colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (255, 0, 255)]  # Far left, left, right, far right
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
    generate_test_sequence(output_dir / "four_sectors.pkl")