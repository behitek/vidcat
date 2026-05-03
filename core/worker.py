import os
import tempfile
import shutil
from PyQt6.QtCore import QThread, pyqtSignal
from core.ffmpeg_utils import normalize_video, concat_videos
from core.inpainting import remove_watermark

class ProcessingWorker(QThread):
    group_started = pyqtSignal(int)
    frame_progress = pyqtSignal(int, int)
    group_done = pyqtSignal(int)
    group_failed = pyqtSignal(int, str)
    all_done = pyqtSignal(int, int) # completed, failed
    
    def __init__(self, videos, output_dir, group_size, remove_watermark_flag, remove_sound, prefix):
        super().__init__()
        self.videos = videos
        self.output_dir = output_dir
        self.group_size = group_size
        self.remove_watermark_flag = remove_watermark_flag
        self.remove_sound = remove_sound
        self.prefix = prefix
        self.is_cancelled = False
        
    def cancel(self):
        self.is_cancelled = True
        
    def run(self):
        # minimal mock for now to pass initialization test
        pass
