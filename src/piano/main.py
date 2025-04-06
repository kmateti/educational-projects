import time
import pyrealsense2 as rs
import numpy as np
import cv2
import argparse
import os
import math
from dataclasses import dataclass

from src.piano.tone_generator import ToneGenerator
from src.piano.key import Key, AngularBounds, C_MAJOR_FREQUENCIES, get_frequency_from_distance
from src.detectors.bounding_box_detector import get_angular_detection
from src.io.frames import get_color_and_depth_frames, FrameData

# Initialize keys with angular bounds
KEYS = [
    Key("Left", (0, 0, 255), AngularBounds(-30, -10)),
    Key("Center", (0, 255, 0), AngularBounds(-10, 10)),
    Key("Right", (255, 0, 0), AngularBounds(10, 30))
]

def overlay_bounding_boxes(frame_data: FrameData, keys: list[Key]):
    """Overlays angular sectors and returns their detections."""
    
    detections = []
    for idx, key in enumerate(keys):
        detection = get_angular_detection(frame_data, key.angular_bounds, key.name, key.color)
        
        if detection is None:
            continue

        # Draw the detection info
        text_y = 30 + (idx * 30)
        note = key.get_note(detection.min_distance_m)
        text = f"{key.name}: {detection.min_distance_m:.2f}m, Az: {detection.azimuth_deg:.1f}°"
        if note:
            text += f" Note: {note}"
            
        cv2.putText(
            frame_data.color_image_rgb, 
            text,
            (10, text_y), 
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            key.color,
            2
        )
        
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
        
        while True:
            loop_start = time.time()
            
            frame_data = get_color_and_depth_frames(pipeline, align)
            if frame_data is None:
                continue
                
            frame_time = time.time() - loop_start
            
            process_start = time.time()
            color_image_with_overlay, detections = overlay_bounding_boxes(frame_data, KEYS)
            process_time = time.time() - process_start
            
            frame_count += 1
            if frame_count % 30 == 0:  # Print stats every 30 frames
                elapsed = time.time() - start_time
                fps = frame_count / elapsed
                print(f"FPS: {fps:.1f}, Frame time: {frame_time*1000:.1f}ms, Process time: {process_time*1000:.1f}ms")
            
            # Update frequencies based on detections
            frequencies = [get_frequency_from_distance(detection.min_distance_m) for detection in detections]
            tone_gen.set_frequencies(frequencies)

            cv2.imshow('RealSense with Bounding Box', color_image_with_overlay)
            key = cv2.waitKey(10)
            if key & 0xFF == ord('q') or key == 27:
                cv2.destroyAllWindows()
                break

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
