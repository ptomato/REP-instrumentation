import numpy as N
import VideoCapture

from Camera import *

class DirectShow(Camera):
    '''Camera that interfaces through DirectShow'''
    
    def __init__(self, *args, **kwargs):
        Camera.__init__(self, args, kwargs)
        self._cam = None
    
    def open(self):
        self._cam = VideoCapture.Device(self.camera_number)
    
    def close(self):
        del self._cam
        self._cam = None
    
    def query_frame(self):
        buffer, width, height = self._cam.getBuffer()
        self.frame = N.ndarray(shape=(width, height, 3), buffer=buffer)
    