import pyaudio
import numpy as np
import collections
from logger import logger
from utils import handle_errors

class AudioStream:
    """Handles microphone audio streaming and buffering."""
    
    def __init__(self, rate: int = 16000, chunk_size: int = 512):
        self.rate = rate
        self.chunk_size = chunk_size
        self.pa = pyaudio.PyAudio()
        self.stream = None
        self.is_running = False

    @handle_errors("Audio")
    def start(self):
        """Starts the microphone stream."""
        if self.stream:
            return

        self.stream = self.pa.open(
            rate=self.rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        self.is_running = True
        logger.info("Microphone stream started.")

    def stop(self):
        """Stops the microphone stream."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        self.is_running = False
        logger.info("Microphone stream stopped.")

    def read(self) -> np.ndarray:
        """Reads a chunk of audio from the stream."""
        if not self.stream:
            return np.array([], dtype=np.int16)
        
        try:
            data = self.stream.read(self.chunk_size, exception_on_overflow=False)
            return np.frombuffer(data, dtype=np.int16)
        except Exception as e:
            logger.warning(f"Audio read error: {e}")
            return np.array([], dtype=np.int16)

    def __del__(self):
        self.stop()
        self.pa.terminate()
