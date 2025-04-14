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
from src.piano.key import Key, C_MAJOR_FREQUENCIES, get_frequency_from_distance, Sector, AngularBounds
from src.detectors.bounding_box_detector import get_angular_detection, get_bounding_box_detections, SectorDetection
from src.io.frames import get_color_and_depth_frames, FrameData

# Define boxes in camera coordinate system
KEYS = [
    Key("Key 1", (0, 0, 255), 
        ((-0.4, -0.3, 0.5),   # min bounds (x, y, z)
         (-0.2, 0.3, 2.0))),  # max bounds
    Key("Key 2", (0, 255, 0), 
        ((-0.1, -0.3, 0.5),
         (0.1, 0.3, 2.0))),
    Key("Key 3", (255, 0, 0), 
        ((0.2, -0.3, 0.5),
         (0.4, 0.3, 2.0))),
    Key("Key 4", (255, 0, 255), 
        ((0.5, -0.3, 0.5),
         (0.7, 0.3, 2.0)))
]

# Calculate sector size (86° FOV divided into 9 sections, using 4 sectors)
SECTOR_WIDTH = 86 / 9  # ~9.56 degrees

SECTORS = [
    Sector("Far Left", (0, 0, 255), 
           AngularBounds(azimuth_center=-43 + SECTOR_WIDTH, 
                        azimuth_span=SECTOR_WIDTH*2)),
           
    Sector("Left", (0, 255, 0), 
           AngularBounds(azimuth_center=-43 + 3*SECTOR_WIDTH,
                        azimuth_span=SECTOR_WIDTH*2)),
           
    Sector("Right", (255, 0, 0), 
           AngularBounds(azimuth_center=-43 + 5*SECTOR_WIDTH,
                        azimuth_span=SECTOR_WIDTH*2)),
           
    Sector("Far Right", (255, 0, 255), 
           AngularBounds(azimuth_center=-43 + 7*SECTOR_WIDTH,
                        azimuth_span=SECTOR_WIDTH*2))
]

class PerformanceMonitor:
    def __init__(self, window_size=30):
        self.times: Dict[str, List[float]] = {}
        self.window_size = window_size
    
    def record(self, name: str, time_ms: float):
        if name not in self.times:
            self.times[name] = []
        self.times[name].append(time_ms)
        if len(self.times[name]) > self.window_size:
            self.times[name].pop(0)
    
    def get_stats(self) -> str:
        stats = []
        for name, times in self.times.items():
            avg = sum(times) / len(times)
            max_t = max(times)
            stats.append(f"{name}: {avg:.1f}ms (max: {max_t:.1f}ms)")
        return " | ".join(stats)

def overlay_bounding_boxes(frame_data: FrameData, keys: list[Key]):
    """Optimized overlay function."""
    detections = []
    
    # Pre-calculate depth conversion once
    depths = frame_data.depth_image.astype(float) / 1000.0
    
    # Process all boxes in parallel using numpy operations
    for idx, key in enumerate(keys):
        detection, color_image_rgb = get_bounding_box_detections(frame_data, key.bounds, key.name, key.color)
        
        if detection is not None:
            detections.append(detection)
            
            # Reduce text overlay overhead
            if idx < 4:  # Only show first 3 keys' stats
                text_y = 30 + (idx * 30)
                note = key.get_note(detection.min_distance_m, detection.num_valid_points)
                overlay_text = f"{key.name}: {detection.min_distance_m:.1f}m"
                cv2.putText(color_image_rgb, overlay_text, 
                           (10, text_y), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.7, key.color, 2)
    
    return color_image_rgb, detections

def overlay_sectors(frame_data: FrameData, sectors: list[Sector]) -> tuple[np.ndarray, list[SectorDetection]]:
    """Overlay angular sectors and return their detections."""
    detections = []
    
    for sector in sectors:
        detection = get_angular_detection(frame_data, sector.bounds, sector.name, sector.color)
        if detection is not None:
            detections.append(detection)
    
    return frame_data.color_image_rgb, detections

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
        
        perf = PerformanceMonitor()
        
        while True:
            frame_start = time.time()
            
            # Get frames
            t0 = time.time()
            frame_data = get_color_and_depth_frames(pipeline, align)
            if frame_data is None:
                continue
            perf.record("Frame", (time.time() - t0) * 1000)
            
            # Process frames using sectors instead of boxes
            t0 = time.time()
            color_image_with_overlay, detections = overlay_sectors(frame_data, SECTORS)
            perf.record("Process", (time.time() - t0) * 1000)
            
            # Update audio
            t0 = time.time()
            frequencies = [get_frequency_from_distance(d.min_distance_m) for d in detections]
            tone_gen.set_frequencies(frequencies)
            perf.record("Audio", (time.time() - t0) * 1000)
            
            # Display results
            if frame_count % 30 == 0:
                stats = perf.get_stats()
                cv2.putText(color_image_with_overlay, stats, 
                           (10, color_image_with_overlay.shape[0] - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
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
