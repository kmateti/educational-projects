"""
Listen to the microphone and show an overlay of the detected notes on the camera feed.
This example uses the integrated webcam and microphone. Press "s" to switch camera, "m" to switch microphone.
"""
import tkinter as tk
from PIL import Image, ImageTk
import cv2
from src.piano.voices import C_MAJOR_FREQUENCIES  # Import the C major note mapping
import argparse
from microphone import Microphone
from camera import Camera

class TunerApp:
    def __init__(self, camera:Camera, microphone:Microphone):
        """
        Constructor
        """
        self.camera = camera
        self.microphone = microphone

        # Create the Tkinter root window
        self.root = tk.Tk()
        self.root.title("Tuner - Camera Feed")

        # Create a Label to display the video frame
        self.video_label = tk.Label(self.root)
        self.video_label.grid(row=0, column=0)

        # Frame for labels and data
        self.text_frame = tk.Frame(self.root)  # Frame to hold labels and entries
        self.text_frame.grid(row=1, column=0)

        self.cam_label = tk.Label(self.text_frame, text=f"Cam: {self.camera.index}")
        self.cam_label.grid(row=0, column=1, padx=100)
    
        self.mic_label = tk.Label(self.text_frame, text=f"Mic: {self.microphone.index}")
        self.mic_label.grid(row=1, column=1, padx=100)

        self.freq_label = tk.Label(self.text_frame, text="Frequency: 0 Hz")
        self.freq_label.grid(row=0, column=0, padx=100, sticky=tk.W)

        self.note_label = tk.Label(self.text_frame, text="Note:")
        self.note_label.grid(row=1, column=0, padx=100, sticky=tk.W)

        self.delta_label = tk.Label(self.text_frame, text="Delta: 0 Hz")
        self.delta_label.grid(row=2, column=0, padx=100, sticky=tk.W)

        # Bind key press events to the root window.
        self.root.bind('s', self.__on_switch_camera)
        self.root.bind('m', self.__on_switch_microphone)

    def run(self):
        """
        Main running loop
        """
        # Start updating the video frames.  The function calls itself repeatedly.
        if self.camera.cap is not None:
            self.__update_opencv_frame(self.video_label, self.camera.cap)

        # Tkinter main loop.  This needs to run to keep the window open and the video updating.
        self.root.mainloop()

    @staticmethod
    def freq_to_note(freq: float) -> str:
        """Map a frequency to the closest musical note using C_MAJOR_FREQUENCIES."""
        if freq <= 0:
            return ""
        # Find the note from C_MAJOR_FREQUENCIES with the smallest absolute difference.
        note, note_freq = min(C_MAJOR_FREQUENCIES.items(), key=lambda item: abs(item[1] - freq))
        return note

    def __update_opencv_frame(self, label, cap):
        """
        Updates the Tkinter label with the latest frame from the OpenCV video capture.

        Args:
            label: The Tkinter Label widget to display the video frame.
            cap: The OpenCV VideoCapture object.
        """
        ret, frame = cap.read()  # Read a frame from the video capture
        if ret:
            # Convert the OpenCV frame to a PIL Image
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Corrected color conversion
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)  # Convert PIL Image to PhotoImage

            # Update the Label with the new image
            label.imgtk = imgtk  # Keep a reference!
            label.configure(image=imgtk)

            #Update stats
            self.cam_label["text"] = f"Cam: {self.camera.index}"
            self.mic_label["text"] = f"Mic: {self.microphone.index}"

            note_text = self.freq_to_note(self.microphone.detected_frequency)
            self.freq_label["text"] = f"Frequency: {self.microphone.detected_frequency:.1f} Hz"
            self.note_label["text"] = f"Note: {note_text}"

            target_freq = C_MAJOR_FREQUENCIES.get(note_text, None)
            diff_text = None
            diff_color = (255, 255, 255)
            if target_freq is not None:
                diff = self.microphone.detected_frequency - target_freq
                diff_color = (255, 0, 0) if diff < 0 else (0, 0, 255)
                diff_text = f"Delta: {diff:+.1f} Hz"        
            self.delta_label["text"] = diff_text

        # Schedule the next update.  This creates a loop.
        label.after(10, self.__update_opencv_frame, label, cap) # 10 millisecond delay

    def __on_switch_camera(self, event):
        """
        Handles switching to the next camera index
        """
        print(f"Switching camera: current camera index {self.camera.index}")
        self.camera.switch()
        print(f"Switching to camera index {self.camera.index}")

    def __on_switch_microphone(self, event):
        """
        Handles switching to the next microphone index
        """
        print(f"Switching microphone: current mic index {self.microphone.index}")
        self.microphone.switch()
        print(f"Switching to microphone index {self.microphone.index}")

def main():
    microphone = Microphone()
    camera = Camera()
    
    #Create command-line parameters
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', "--microphone_index", type=int, default=-1, help="Index of microphone to use")
    parser.add_argument('-n', "--microphone_max_index", type=int, default=5, help="Maximum number of indexes to check when looking for a microphone")
    parser.add_argument('-c', "--camera_index",  type=int, default=-1, help="Index of camera to use")
    parser.add_argument('-d', "--camera_max_index", type=int, default=5, help="Maximum number of indexes to check when looking for a camera")

    #Parse command-line parameters
    args = parser.parse_args()

    mic_index = microphone.start(args.microphone_index, args.microphone_max_index)
    if ((args.microphone_index >= 0) and (mic_index != args.microphone_index)):
        print(f"Unable to use microphone with index {args.microphone_index}!")
        return
    elif (mic_index < 0):
        print(f"Unable to find a microphone to use!")
        return

    cam_index = camera.start(args.camera_index, args.camera_max_index)
    if ((args.camera_index >= 0) and (cam_index != args.camera_index)):
        print(f"Unable to use camera with index {args.camera_index}!")
        return
    elif (cam_index < 0):
        print(f"Unable to find a camera to use!")
        return

    app = TunerApp(camera, microphone)
    app.run()

if __name__ == "__main__":
    main()
