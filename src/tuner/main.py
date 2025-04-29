"""
Listen to the microphone and show an overlay of the detected notes on the camera feed.
This example uses the integrated webcam and microphone.
"""

import cv2
import numpy as np
import pyaudio
import time
from src.piano.voices import C_MAJOR_FREQUENCIES  # Import the C major note mapping

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
    Estimate the predominant frequency in the given audio snippet using a FFT-based approach.
    """
    # Convert bytes to numpy array of float32; the stream format is paFloat32
    audio_np = np.frombuffer(audio_data, dtype=np.float32)
    # Apply a Hann window to reduce spectral leakage
    window = np.hanning(len(audio_np))
    audio_np = audio_np * window
    # Compute the FFT and corresponding frequencies
    fft_vals = np.fft.rfft(audio_np)
    freqs = np.fft.rfftfreq(len(audio_np), d=1.0/rate)
    magnitudes = np.abs(fft_vals)
    # Find the peak in the magnitude spectrum
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

def start_audio_stream():
    """
    Initialize and start a PyAudio stream that uses a callback for realtime pitch detection.
    """
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=44100,
                    input=True,
                    frames_per_buffer=2048,
                    stream_callback=audio_callback)
    stream.start_stream()
    return p, stream

def main():
    global detected_frequency

    # Start the microphone listener
    pa, audio_stream = start_audio_stream()
    
    # Open webcam (integrated camera)
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("Unable to open camera!")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to get frame from camera")
            break

        # Optionally flip the frame for a mirror effect
        frame = cv2.flip(frame, 1)
        
        # Map the detected frequency to a note using the C_MAJOR_FREQUENCIES mapping.
        note_text = freq_to_note(detected_frequency)
        display_text = f"Freq: {detected_frequency:.1f} Hz, Note: {note_text}"
        cv2.putText(frame, display_text, (30, 40), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 255, 0), 2, cv2.LINE_AA)
        
        # If the note was found in C_MAJOR_FREQUENCIES, compute the difference.
        target_freq = C_MAJOR_FREQUENCIES.get(note_text, None)
        if target_freq is not None:
            diff = detected_frequency - target_freq
            # Choose blue if detected frequency is lower than the target, red if higher.
            diff_color = (255, 0, 0) if diff < 0 else (0, 0, 255)
            diff_text = f"Delta: {diff:+.1f} Hz"
            cv2.putText(frame, diff_text, (30, 80), cv2.FONT_HERSHEY_SIMPLEX,
                        1, diff_color, 2, cv2.LINE_AA)
        
        cv2.imshow("Tuner - Camera Feed", frame)
        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Cleanup resources
    cap.release()
    cv2.destroyAllWindows()
    audio_stream.stop_stream()
    audio_stream.close()
    pa.terminate()

if __name__ == "__main__":
    main()
