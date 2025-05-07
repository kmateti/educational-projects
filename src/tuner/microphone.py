import pyaudio
import numpy as np

class Microphone:
    
    def __init__(self):
        """
        Constructor
        """
        self.pa = None
        self.audio_stream = None
        self.index = 0
        self.max_index = 1
        # Store the detected pitch (in Hz)
        self.detected_frequency = 0.0

    def __del__(self):
        """
        Destructor
        """
        if self.audio_stream is not None:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        if self.pa is not None:
            self.pa.terminate()


    def start(self, index:int, max_index:int) -> int:
        """
        Initialize a microphone
        """
        self.max_index = max_index
        if index >= 0:
            # Start the microphone listener with the current mic device.
            self.pa, self.audio_stream = self.__start_audio_stream(index)
            if self.pa != None and self.audio_stream != None:
                self.index = index
                return index
        else:
            #Try to find a microphone
            for index in range(0, max_index):
                self.pa, self.audio_stream = self.__start_audio_stream(index)
                if self.pa != None and self.audio_stream != None:
                    self.index = index
                    return index

        return -1
    
    def switch(self):
        """
        Switch microphone: Close the current audio stream and try the next microphone.
        """
        self.audio_stream.stop_stream()
        self.audio_stream.close()
        self.pa.terminate()
        self.index = (self.index + 1) % self.max_index
        try:
            pa, audio_stream = self.__start_audio_stream(self.index)
        except Exception as e:
            self.index = 0
            pa, audio_stream = self.__start_audio_stream(self.index)

    def __detect_pitch(self, audio_data: bytes, rate: int) -> float:
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

    def __audio_callback(self, in_data, frame_count, time_info, status):
        """
        A PyAudio callback to process incoming microphone data.
        """
        sample_rate = 44100
        try:
            self.detected_frequency = self.__detect_pitch(in_data, sample_rate)
        except Exception as e:
            print("Pitch detection error:", e)
        return (in_data, pyaudio.paContinue)

    def __start_audio_stream(self, mic_index=None):
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
                        stream_callback=self.__audio_callback)
        stream.start_stream()
        return p, stream
