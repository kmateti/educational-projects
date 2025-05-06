import argparse

class MainArgs:

    def __init__(self):
        """
        Initialize the program arguments and set up command line information
        """
        self.microphone_index = -1
        self.microphone_max_index = 5
        self.camera_index = -1
        self.camera_max_index = 5
        
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('-m', "--microphone_index", type=int, help="Index of microphone to use")
        self.parser.add_argument('-n', "--microphone_max_index", type=int, help="Maximum number of indexes to check when looking for a microphone")
        self.parser.add_argument('-c', "--camera_index",  type=int, help="Index of camera to use")
        self.parser.add_argument('-d', "--camera_max_index", type=int, help="Maximum number of indexes to check when looking for a camera")

    def parse_args(self):
        """
        Parse the command line arguments to potentially update the program arguments
        """
        # Parse the arguments
        args = self.parser.parse_args()
        if args.microphone_index != None:
            self.microphone_index = args.microphone_index
        if args.microphone_max_index != None:
            self.microphone_max_index = args.microphone_max_index
        if args.camera_index != None:
            self.camera_index = args.camera_index
        if args.camera_max_index != None:
            self.camera_max_index = args.camera_max_index


