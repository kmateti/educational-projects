import time
import pyrealsense2 as rs
import numpy as np
import cv2
import argparse
import os
import math
from typing import Dict, List, Tuple

from src.piano.tone_generator import ToneGenerator
from src.detectors.angular_detector import Sector, AngularBounds, SectorDetection
from src.io.frames import get_color_and_depth_frames, FrameData
from src.piano.config_loader import load_config  # Loads sector configurations
from src.piano.voices import SectorDistanceToNoteMapper

# Load sector configurations from YAML
sector_configs: Dict[str, any] = load_config("src/piano/config.yaml")

# Build dynamic list of SectorWithMapper objects from YAML
class SectorWithMapper:
    """Encapsulates a Sector and its corresponding SectorDistanceToNoteMapper."""
    def __init__(self, name: str, config: dict):
        self.name = name
        self.sector = self._create_sector(config)
        self.mapper = self._create_mapper(config)

    def _create_sector(self, config: dict) -> Sector:
        bounds = AngularBounds(
            azimuth_center=config.ray.azimuth_center,
            azimuth_span=config.ray.azimuth_span,
            elevation_center=getattr(config.ray, "elevation_center", 0),
            elevation_span=getattr(config.ray, "elevation_span", 0),
            min_range=getattr(config.ray, "min_range", 0.5),
            max_range=getattr(config.ray, "max_range", 2.6)
        )
        return Sector(self.name, config.color, bounds)

    def _create_mapper(self, config: dict) -> SectorDistanceToNoteMapper:
        return SectorDistanceToNoteMapper(config.note_mapper)

SECTORS_WITH_MAPPERS: List[SectorWithMapper] = [
    SectorWithMapper(name, s_conf) for name, s_conf in sector_configs.items()
]

NUM_POINTS = 50 * 50  # Minimum number of valid points for a valid detection

def get_discrete_color(index: int, total: int) -> tuple[int, int, int]:
    """
    Generate a discrete color from a continuous HSV colormap.
    The hue is spread evenly over the range [0, 180] (OpenCV HSV hue range).
    """
    hue = int((index / total) * 180)
    hsv = np.uint8([[[hue, 255, 255]]])
    bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0][0]
    return tuple(int(c) for c in bgr)


def overlay_sectors(frame_data: FrameData,
                    sectors_with_mappers: List[SectorWithMapper]
                   ) -> Tuple[np.ndarray, List[Tuple[SectorDetection, SectorWithMapper]]]:
    """
    Overlay sector detections on the color image using text that reflects the ray configuration.
    The text color for each sector is chosen based on the discrete color corresponding to the note range.
    """
    overlay_image = frame_data.color_image_rgb.copy()
    blended = overlay_image.copy()
    
    # Convert depth image (in millimeters) to meters.
    depths = frame_data.depth_image.astype(float) / 1000.0
    
    # Calculate the horizontal FOV of the camera from intrinsics.
    width = frame_data.depth_intrinsics.width
    fx = frame_data.depth_intrinsics.fx
    h_fov = 2 * np.rad2deg(np.arctan(width / (2 * fx)))
    
    detections: List[Tuple[SectorDetection, SectorWithMapper]] = []
    
    for swm in sectors_with_mappers:
        detection = swm.sector.detect(frame_data)
        if detection is None or detection.num_valid_points <= NUM_POINTS:
            continue
        
        # Determine which note interval the detection.min_distance_m falls into.
        total_ranges = len(swm.mapper.ranges)
        note_index = total_ranges - 1  # Default to last range.
        for idx, (d_min, d_max, _) in enumerate(swm.mapper.ranges):
            if d_min <= detection.min_distance_m < d_max:
                note_index = idx
                break
        
        discrete_color = get_discrete_color(note_index, total_ranges)
        
        # Use the note mapper to get note label (optional)
        note_label = swm.mapper.get_note_from_distance(detection.min_distance_m)
        
        # Compute text x position using the sector's azimuth_center.
        img_width = overlay_image.shape[1]
        x_pos = int(((swm.sector.bounds.azimuth_center + h_fov/2) / h_fov) * img_width)
        
        cv2.putText(blended, f"{swm.sector.name}", (x_pos, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, discrete_color, 2)
        cv2.putText(blended, f"Dist: {detection.min_distance_m:.1f}m", (x_pos, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, discrete_color, 2)
        cv2.putText(blended, f"Note: {note_label}", (x_pos, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, discrete_color, 2)
        cv2.putText(blended, f"Points: {detection.num_valid_points}", (x_pos, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, discrete_color, 2)
        
        # Apply discrete color overlay for each note range.
        color_overlay = np.zeros_like(overlay_image)
        color_overlay[detection.valid_mask] = discrete_color
        blended = cv2.addWeighted(blended, 1.0, color_overlay, 0.4, 0)
        
        detections.append((detection, swm))
    
    return blended, detections

def main(bag_file=None):
    try:
        if bag_file and not os.path.exists(bag_file):
            raise FileNotFoundError(f"The specified .bag file does not exist: {bag_file}")

        pipeline = rs.pipeline()
        config = rs.config()
        if bag_file:
            rs.config.enable_device_from_file(config, bag_file)
        
        config.enable_stream(rs.stream.depth)
        config.enable_stream(rs.stream.color)
        pipeline_profile = pipeline.start(config)
        
        depth_stream = pipeline_profile.get_stream(rs.stream.depth).as_video_stream_profile()
        color_stream = pipeline_profile.get_stream(rs.stream.color).as_video_stream_profile()

        depth_intrinsics = depth_stream.get_intrinsics()
        color_intrinsics = color_stream.get_intrinsics()

        print(f"Depth: {depth_intrinsics.width}x{depth_intrinsics.height} @ {depth_stream.fps()} FPS")
        print(f"Color: {color_intrinsics.width}x{color_intrinsics.height} @ {color_stream.fps()} FPS")

        align_to = rs.stream.color
        align = rs.align(align_to)

        tone_gen = ToneGenerator()
        tone_gen.start()

        frame_count = 0
        start_time = time.time()

        while True:
            frame_data = get_color_and_depth_frames(pipeline, align)
            if frame_data is None:
                continue
            
            overlay_image, detections = overlay_sectors(frame_data, SECTORS_WITH_MAPPERS)
            
            # For each detection, use the corresponding mapper to get the frequency,
            # then update the tone generator with the obtained frequencies
            frequencies = [
                swm.mapper.get_frequency_from_distance(detection.min_distance_m)
                for detection, swm in detections
            ]
            tone_gen.set_frequencies(frequencies)
            
            cv2.imshow('RealSense with Sectors', overlay_image)
            if cv2.waitKey(1) in [ord('q'), 27]:
                break
            frame_count += 1
            
    except Exception as e:
        print(e)
        raise
    finally:
        if 'pipeline' in locals():
            pipeline.stop()
        if 'tone_gen' in locals():
            tone_gen.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RealSense depth and color viewer with sector overlay.")
    parser.add_argument("--bag", type=str, help="Path to a .bag file to replay from.")
    args = parser.parse_args()
    main(args.bag)
