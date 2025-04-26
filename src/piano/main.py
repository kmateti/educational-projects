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

def overlay_sectors(frame_data: FrameData,
                    sectors_with_mappers: List[SectorWithMapper]
                   ) -> Tuple[np.ndarray, List[Tuple[SectorDetection, SectorWithMapper]]]:
    """Overlay sector detections on the color image and return detections with their corresponding SectorWithMapper."""
    overlay_image = frame_data.color_image_rgb.copy()
    blended = overlay_image.copy()
    detections: List[Tuple[SectorDetection, SectorWithMapper]] = []
    
    # Convert the depth colormap image to RGB once (for overlaying)
    depth_rgb = cv2.cvtColor(frame_data.depth_colormap_image, cv2.COLOR_BGR2RGB)
    
    for swm in sectors_with_mappers:
        detection = swm.sector.detect(frame_data)
        if detection is not None and detection.num_valid_points > NUM_POINTS:
            note = swm.mapper.get_note_from_distance(detection.min_distance_m)
            
            # Create an overlay using the valid mask from the detection
            valid_mask = detection.valid_mask
            alpha = 0.4
            depth_section = np.zeros_like(overlay_image)
            depth_section[valid_mask] = depth_rgb[valid_mask]
            cv2.addWeighted(blended, 1.0, depth_section, alpha, 0, blended)
            
            # Determine text position based on the detected azimuth
            img_width = blended.shape[1]
            angle_range = 86  # Total FOV; adjust as needed
            x_pos = int((detection.azimuth_deg + 43) * img_width / angle_range)
            
            # Overlay text information on the blended image
            text = f"{swm.sector.name}: {detection.min_distance_m:.1f}m"
            cv2.putText(blended, text, (x_pos, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, swm.sector.color, 2)
            cv2.putText(blended, f"Note: {note}", (x_pos, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, swm.sector.color, 2)
            cv2.putText(blended, f"Points: {detection.num_valid_points}", (x_pos, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, swm.sector.color, 2)
            
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
