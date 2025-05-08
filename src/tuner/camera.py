import cv2

class Camera:
    
    def __init__(self):
        """
        Constructor
        """
        self.index = 0
        self.max_index = 1
        self.cap = None

    def __del__(self):
        """
        Destructor
        """
        if self.cap is not None:
            self.cap.release()

    def start(self, index:int, max_index:int) -> int:
        """
        Initialize a camera
        """
        self.max_index = max_index
        if index >= 0:
            #Start the camera chosen
            self.cap = self.__open_camera(index)
            if self.cap is not None and self.cap.isOpened():
                self.index = index
                return self.index
            
        else:
            #Try to find a camera
            for i in range(0, max_index):
                self.cap = self.__open_camera(i)
                if self.cap is not None and self.cap.isOpened():
                    self.index = i
                    return self.index

        return -1
            
    def switch(self):
        """
        Switch camera index: Release current camera and try the next index.
        """
        self.cap.release()
        self.index = (self.index + 1) % self.max_index
        self.cap = self.__open_camera(self.index)
        if not self.cap.isOpened():
            self.index = 0
            self.cap = self.__open_camera(self.index)

    def __open_camera(self, index:int):
        """
        Start capturing on a camera index
        """
        return cv2.VideoCapture(index)