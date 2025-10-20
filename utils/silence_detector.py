import webrtcvad
import numpy as np
from config.logging import get_logger

logger = get_logger(__name__)

class WebRTCVAD:
    def __init__(self, mode=3):
        """
        Initialize the WebRTC VAD.
        
        Args:
            mode (int): Aggressiveness mode (0-3). Higher values are more aggressive in detecting speech.
                        0: Least aggressive
                        3: Most aggressive
        """
        self.vad = webrtcvad.Vad(mode)
        self.sample_rate = 16000  # WebRTC VAD requires 8000, 16000, 32000, or 48000 Hz
        self.frame_duration_ms = 20  # Frame duration in ms (10, 20, or 30)
        self.frame_size = int(self.sample_rate * self.frame_duration_ms / 1000) * 2  # Bytes per frame (16-bit PCM)

    def is_speech(self, audio_chunk):
        """
        Detect if the audio chunk contains speech.

        Args:
            audio_chunk (bytes): Audio chunk in PCM format.

        Returns:
            bool: True if speech is detected, False otherwise.
        """
        try:
            frames = self.split_into_frames(audio_chunk)
            for frame in frames:
                if self.vad.is_speech(frame, self.sample_rate):
                    return True
            return False

        except Exception as e:
            logger.error(f"Error detecting speech: {e}")
            return False

    def split_into_frames(self, audio_chunk):
        """
        Split audio chunk into fixed-size frames for WebRTC VAD.

        Args:
            audio_chunk (bytes): Audio chunk in PCM format.

        Returns:
            list[bytes]: List of frames of the required size.
        """
        frames = []
        for i in range(0, len(audio_chunk), self.frame_size):
            frame = audio_chunk[i:i + self.frame_size]
            if len(frame) == self.frame_size:  # Ignore incomplete frames
                frames.append(frame)
        return frames
    
    def is_low_energy(self, audio_chunk, threshold=0.01):
        """Check if audio chunk has low energy."""
        audio = np.frombuffer(audio_chunk, dtype=np.int16)
        energy = np.sqrt(np.mean(audio**2))
        return energy < threshold


