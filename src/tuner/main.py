"""
Listen to the microphone and show an overlay of the detected notes on the camera feed.
This example uses the integrated webcam and microphone. Press "s" to switch camera, "m" to switch microphone.
"""
import tkinter as tk
from PIL import Image, ImageTk
import cv2
import numpy as np
import time
from src.piano.voices import C_MAJOR_FREQUENCIES  # Import the C major note mapping
from main_args import MainArgs
from microphone import Microphone
from camera import Camera

commandline_args = MainArgs()
microphone = Microphone()
camera = Camera()

def freq_to_note(freq: float) -> str:
    """Map a frequency to the closest musical note using C_MAJOR_FREQUENCIES."""
    if freq <= 0:
        return ""
    # Find the note from C_MAJOR_FREQUENCIES with the smallest absolute difference.
    note, note_freq = min(C_MAJOR_FREQUENCIES.items(), key=lambda item: abs(item[1] - freq))
    return note

def draw_main_overlay(frame, display_text, diff_text=None, diff_color=(255,255,255)):
    """
    Draws a 50% transparent black box with the main display text and (optionally) the delta text.
    """
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    thickness = 2
    pad_x, pad_y = 16, 12  # Padding around text

    # Get text sizes
    (text_w, text_h), _ = cv2.getTextSize(display_text, font, font_scale, thickness)
    diff_w, diff_h = 0, 0
    if diff_text:
        (diff_w, diff_h), _ = cv2.getTextSize(diff_text, font, font_scale, thickness)
    box_width = max(text_w, diff_w) + 2 * pad_x
    box_height = text_h + (diff_h if diff_text else 0) + 3 * pad_y

    # Top-left corner of the box
    box_x, box_y = 20, 20

    # Draw the transparent rectangle
    overlay = frame.copy()
    cv2.rectangle(overlay, (box_x, box_y), (box_x + box_width, box_y + box_height), (0, 0, 0), -1)
    alpha = 0.5
    frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

    # Draw the text on top of the box
    text_org = (box_x + pad_x, box_y + pad_y + text_h)
    cv2.putText(frame, display_text, text_org, font, font_scale, (0, 255, 0), thickness, cv2.LINE_AA)
    if diff_text:
        diff_org = (box_x + pad_x, box_y + pad_y + text_h + pad_y + diff_h)
        cv2.putText(frame, diff_text, diff_org, font, font_scale, diff_color, thickness, cv2.LINE_AA)
    return frame

def main():
    #Parse any command-line parameters
    commandline_args.parse_args()

    mic_index = microphone.start(commandline_args.microphone_index, commandline_args.microphone_max_index)
    if ((commandline_args.microphone_index >= 0) and (mic_index != commandline_args.microphone_index)):
        print(f"Unable to use microphone with index {commandline_args.microphone_index}!")
        return
    elif (mic_index < 0):
        print(f"Unable to find a microphone to use!")
        return

    cam_index = camera.start(commandline_args.camera_index, commandline_args.camera_max_index)
    if ((commandline_args.camera_index >= 0) and (cam_index != commandline_args.camera_index)):
        print(f"Unable to use camera with index {commandline_args.camera_index} - logic check - {cam_index}!")
        return
    elif (cam_index < 0):
        print(f"Unable to find a camera to use!")
        return

    while True:
        ret, frame = camera.cap.read()
        if not ret:
            print("Failed to get frame from camera")
            break

        frame = cv2.flip(frame, 1)
        note_text = freq_to_note(microphone.detected_frequency)
        display_text = f"Freq: {microphone.detected_frequency:.1f} Hz, Note: {note_text}"
        target_freq = C_MAJOR_FREQUENCIES.get(note_text, None)
        diff_text = None
        diff_color = (255, 255, 255)
        if target_freq is not None:
            diff = microphone.detected_frequency - target_freq
            diff_color = (255, 0, 0) if diff < 0 else (0, 0, 255)
            diff_text = f"Delta: {diff:+.1f} Hz"

        frame = draw_main_overlay(frame, display_text, diff_text, diff_color)

        # Overlay current video and audio source info on the bottom-right
        height, width, _ = frame.shape
        source_text = f"Cam: {cam_index} | Mic: {mic_index}"
        cv2.putText(frame, source_text, (width - 300, height - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        
        cv2.imshow("Tuner - Camera Feed", frame)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord('s'):
            # Switch camera index: release current camera and try the next index.
            print(f"Switching camera: current camera index {camera.index}")
            camera.switch()
            print(f"Switching to camera index {camera.index}")
        elif key == ord('m'):
            # Switch microphone: close the current audio stream and try the next microphone.
            print(f"Switching microphone: current mic index {microphone.index}")
            microphone.switch()
            print(f"Switching to microphone index {microphone.index}")

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
