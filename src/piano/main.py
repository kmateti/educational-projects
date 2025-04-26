import time
import pyrealsense2 as rs
import numpy as np
import cv2
import argparse
import os
import math
from dataclasses import dataclass
from typing import Dict, List

from src.piano.tone_generator import ToneGenerator
from src.piano.voices import get_frequency_from_distance, get_note_from_distance
from src.detectors.angular_detector import Sector, AngularBounds, get_angular_detection, SectorDetection
from src.io.frames import get_color_and_depth_frames, FrameData

# Calculate sector size (86° FOV divided into 9 sections, using 4 sectors)
SECTOR_WIDTH = 86 / 9  # ~9.56 degrees
NUM_POINTS = 50*50  # Minimum number of valid points for detection
SECTORS = [
    Sector("Far Left", (0, 0, 255), 
           AngularBounds(azimuth_center=-43 + SECTOR_WIDTH, 
                        azimuth_span=SECTOR_WIDTH)),
           
    Sector("Left", (0, 255, 0), 
           AngularBounds(azimuth_center=-43 + 3*SECTOR_WIDTH,
                        azimuth_span=SECTOR_WIDTH)),
           
    Sector("Right", (255, 0, 0), 
           AngularBounds(azimuth_center=-43 + 5*SECTOR_WIDTH,
                        azimuth_span=SECTOR_WIDTH)),
           
    Sector("Far Right", (255, 0, 255), 
           AngularBounds(azimuth_center=-43 + 7*SECTOR_WIDTH,
                        azimuth_span=SECTOR_WIDTH))
]

def overlay_sectors(frame_data: FrameData, sectors: list[Sector]) -> tuple[np.ndarray, list[SectorDetection]]:
    """Overlay angular sectors and return their detections."""
    detections = []
    color_image = frame_data.color_image_rgb.copy()
    blended = color_image.copy()
    
    # Convert depth colormap to RGB once
    depth_rgb = cv2.cvtColor(frame_data.depth_colormap_image, cv2.COLOR_BGR2RGB)
    
    for sector in sectors:
        detection = get_angular_detection(frame_data, sector.bounds, sector.name, sector.color)
        if detection is not None and detection.num_valid_points > NUM_POINTS:
            # Get note for current distance
            note = get_note_from_distance(detection.min_distance_m)
            
            # Create mask for this sector's angular bounds
            valid_mask = detection.valid_mask
            
            # Apply depth overlay only within valid mask
            alpha = 0.4
            depth_section = np.zeros_like(color_image)
            depth_section[valid_mask] = depth_rgb[valid_mask]
            cv2.addWeighted(blended, 1.0, depth_section, alpha, 0, blended)
            
            # Calculate text position
            img_width = frame_data.color_image_rgb.shape[1]
            angle_range = 86  # Total FOV
            x_pos = int((detection.azimuth_deg + 43) * img_width / angle_range)
            
            # Add text overlays
            text = f"{sector.name}: {detection.min_distance_m:.1f}m"
            cv2.putText(blended, text,
                       (x_pos, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX,
                       0.7, sector.color, 2)
            
            # Add note below distance
            cv2.putText(blended, f"Note: {note}",
                       (x_pos, 60),
                       cv2.FONT_HERSHEY_SIMPLEX,
                       0.7, sector.color, 2)
            
            # Add note below distance
            cv2.putText(blended, f"Points: {detection.num_valid_points}",
                       (x_pos, 90),
                       cv2.FONT_HERSHEY_SIMPLEX,
                       0.7, sector.color, 2)
            
            detections.append(detection)
    
    return blended, detections

def main(bag_file=None):
    try:
        if bag_file and not os.path.exists(bag_file):
            raise FileNotFoundError(f"The specified .bag file does not exist: {bag_file}")

        pipeline = rs.pipeline()
        config = rs.config()

        if bag_file:
            rs.config.enable_device_from_file(config, bag_file)

        # Enable streams without hardcoding resolution
        config.enable_stream(rs.stream.depth)
        config.enable_stream(rs.stream.color)

        pipeline_profile = pipeline.start(config)

        # Query active stream profiles from the .bag file
        depth_stream = pipeline_profile.get_stream(rs.stream.depth).as_video_stream_profile()
        color_stream = pipeline_profile.get_stream(rs.stream.color).as_video_stream_profile()

        depth_intrinsics = depth_stream.get_intrinsics()
        color_intrinsics = color_stream.get_intrinsics()

        print(f"Depth Stream: {depth_intrinsics.width}x{depth_intrinsics.height} @ {depth_stream.fps()} FPS")
        print(f"Color Stream: {color_intrinsics.width}x{color_intrinsics.height} @ {color_stream.fps()} FPS")

        align_to = rs.stream.color
        align = rs.align(align_to)

        # Create tone generator
        tone_gen = ToneGenerator()
        tone_gen.start()
        frame_count = 0
        start_time = time.time()
                
        while True:
            frame_start = time.time()
            
            # Get frames
            t0 = time.time()
            frame_data = get_color_and_depth_frames(pipeline, align)
            if frame_data is None:
                continue
            
            # Process frames using sectors instead of boxes
            t1 = time.time()
            color_image_with_overlay, detections = overlay_sectors(frame_data, SECTORS)
                    
            # Update audio
            t3 = time.time()
            frequencies = [get_frequency_from_distance(d.min_distance_m) for d in detections]
            tone_gen.set_frequencies(frequencies)
            
            cv2.imshow('RealSense with Bounding Box', color_image_with_overlay)
            if cv2.waitKey(1) in [ord('q'), 27]:
                break
            frame_count += 1
            
    except Exception as e:
        print(e)
        raise e
    finally:
        if 'pipeline' in locals():
            pipeline.stop()
        if 'tone_gen' in locals():
            tone_gen.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RealSense depth and color viewer with bounding box overlay.")
    parser.add_argument("--bag", type=str, help="Path to a .bag file to replay from.")
    args = parser.parse_args()

    main(args.bag)
