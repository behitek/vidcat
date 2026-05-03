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
        groups = [self.videos[i:i + self.group_size] for i in range(0, len(self.videos), self.group_size)]
        completed = 0
        failed = 0
        
        for idx, group in enumerate(groups):
            if self.is_cancelled:
                break
                
            self.group_started.emit(idx)
            
            try:
                # Stub for actual processing
                pass
                
                completed += 1
                self.group_done.emit(idx)
            except Exception as e:
                failed += 1
                self.group_failed.emit(idx, str(e))
                
        self.all_done.emit(completed, failed)
