import os
from datetime import datetime
import wave
from typing import Optional
from config.logging import logger

class AudioSaver:
    def __init__(self, output_dir: str = "audio_recordings"):
        self.output_dir = output_dir
        self.current_file: Optional[wave.Wave_write] = None
        self.ensure_output_dir()
        
    def ensure_output_dir(self):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
    def get_new_filename(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.output_dir, f"recording_{timestamp}.wav")
    
    def start_new_recording(self, channels: int = 1, sample_width: int = 2, framerate: int = 16000):
        if self.current_file:
            self.current_file.close()
            
        filename = self.get_new_filename()
        self.current_file = wave.open(filename, 'wb')
        self.current_file.setnchannels(channels)
        self.current_file.setsampwidth(sample_width)
        self.current_file.setframerate(framerate)
        logger.info(f"Started new recording: {filename}")
        return filename
        
    def write_chunk(self, audio_data: bytes):
        if not self.current_file:
            self.start_new_recording()
        self.current_file.writeframes(audio_data)
        
    def close_current(self):
        if self.current_file:
            self.current_file.close()
            self.current_file = None
