"""
Listen to the microphone and show an overlay of the detected notes on the camera feed.
This example uses the integrated webcam and microphone. Press "s" to switch camera, "m" to switch microphone.
"""

import cv2
import numpy as np
import pyaudio
import time
from src.piano.voices import C_MAJOR_FREQUENCIES  # Import the C major note mapping
from main_args import MainArgs

# Global variable to store the detected pitch (in Hz)
detected_frequency = 0.0

def freq_to_note(freq: float) -> str:
    """Map a frequency to the closest musical note using C_MAJOR_FREQUENCIES."""
    if freq <= 0:
        return ""
    # Find the note from C_MAJOR_FREQUENCIES with the smallest absolute difference.
    note, note_freq = min(C_MAJOR_FREQUENCIES.items(), key=lambda item: abs(item[1] - freq))
    return note

def detect_pitch(audio_data: bytes, rate: int) -> float:
    """
    Estimate the predominant frequency in the given audio snippet using an FFT-based approach.
    """
    audio_np = np.frombuffer(audio_data, dtype=np.float32)
    window = np.hanning(len(audio_np))
    audio_np = audio_np * window
    fft_vals = np.fft.rfft(audio_np)
    freqs = np.fft.rfftfreq(len(audio_np), d=1.0/rate)
    magnitudes = np.abs(fft_vals)
    peak_idx = np.argmax(magnitudes)
    peak_freq = freqs[peak_idx]
    return peak_freq

def audio_callback(in_data, frame_count, time_info, status):
    """
    A PyAudio callback to process incoming microphone data.
    """
    global detected_frequency
    sample_rate = 44100
    try:
        detected_frequency = detect_pitch(in_data, sample_rate)
    except Exception as e:
        print("Pitch detection error:", e)
    return (in_data, pyaudio.paContinue)

def start_audio_stream(mic_index=None):
    """
    Initialize and start a PyAudio stream that uses a callback for realtime pitch detection.
    The input_device_index parameter allows switching the microphone.
    """
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=44100,
                    input=True,
                    input_device_index=mic_index,
                    frames_per_buffer=2048,
                    stream_callback=audio_callback)
    stream.start_stream()
    return p, stream

def open_camera(cam_index):
    return cv2.VideoCapture(cam_index)

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
    global detected_frequency

    #Parse any command-line parameters
    commandline_args = MainArgs()
    commandline_args.parse_args()

    if commandline_args.microphone_index >= 0:
        # Start the microphone listener with the current mic device.
        pa, audio_stream = start_audio_stream(commandline_args.microphone_index)
        if pa != None and audio_stream != None:
            mic_index = commandline_args.microphone_index
    else:
        #Try to find a microphone
        for index in range(0, commandline_args.microphone_max_index):
            pa, audio_stream = start_audio_stream(index)
            if pa != None and audio_stream != None:
                mic_index = index
                break

        if mic_index >= commandline_args.microphone_max_index:
            print(f"Unable to find a microphone to use!")
            return

    if commandline_args.camera_index >= 0:
        #Start the camera chosen
        cap = open_camera(commandline_args.camera_index)
        if cap is None or not cap.isOpened():
            print(f"Unable to open camera with index {commandline_args.camera_index}!")
            return
        
        cam_index = commandline_args.camera_index
    else:
        #Try to find a camera
        for index in range(0, commandline_args.camera_max_index):
            cap = open_camera(index)
            if cap is not None and cap.IsOpened():
                cam_index = index
                break

        if index >= commandline_args.camera_max_index:
            print(f"Unable to find a camera to use!")
            return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to get frame from camera")
            break

        frame = cv2.flip(frame, 1)
        note_text = freq_to_note(detected_frequency)
        display_text = f"Freq: {detected_frequency:.1f} Hz, Note: {note_text}"
        target_freq = C_MAJOR_FREQUENCIES.get(note_text, None)
        diff_text = None
        diff_color = (255, 255, 255)
        if target_freq is not None:
            diff = detected_frequency - target_freq
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
            cap.release()
            cam_index = (cam_index + 1) % commandline_args.camera_max_index
            print(f"Switching to camera index {cam_index}")
            cap = open_camera(cam_index)
            if not cap.isOpened():
                print(f"Camera index {cam_index} is not available, reverting to index 0.")
                cam_index = 0
                cap = open_camera(cam_index)
        elif key == ord('m'):
            # Switch microphone: close the current audio stream and try the next microphone.
            print(f"Switching microphone: current mic index {mic_index}")
            audio_stream.stop_stream()
            audio_stream.close()
            pa.terminate()
            mic_index = (mic_index + 1) % commandline_args.microphone_max_index
            print(f"Switching to microphone index {mic_index}")
            try:
                pa, audio_stream = start_audio_stream(mic_index)
            except Exception as e:
                print(f"Unable to open microphone with index {mic_index}: {e}")
                mic_index = 0
                pa, audio_stream = start_audio_stream(mic_index)

    cap.release()
    cv2.destroyAllWindows()
    audio_stream.stop_stream()
    audio_stream.close()
    pa.terminate()

if __name__ == "__main__":
    main()
