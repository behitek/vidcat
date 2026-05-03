import os
import tempfile
import shutil
import ffmpeg
import subprocess
import re
import imageio_ffmpeg
from PyQt6.QtCore import QThread, pyqtSignal
from core.ffmpeg_utils import normalize_video, concat_videos

class ProcessingWorker(QThread):
    # Signals:
    # int: group_idx
    group_started = pyqtSignal(int)
    # int, int: current_frame, total_frames
    frame_progress = pyqtSignal(int, int)
    # int: group_idx
    group_done = pyqtSignal(int)
    # int, str: group_idx, error message
    group_failed = pyqtSignal(int, str)
    # int, int: completed count, failed count
    all_done = pyqtSignal(int, int)
    
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
                with tempfile.TemporaryDirectory() as temp_dir:
                    # 1. Get target resolution from first video using ffmpeg
                    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                    try:
                        result = subprocess.run([ffmpeg_exe, "-i", group[0]], stderr=subprocess.PIPE, text=True)
                        output = result.stderr
                        # Find "Stream #...: Video: ... 1920x1080"
                        match = re.search(r'Video:.*?\s(\d{3,4})x(\d{3,4})', output)
                        if not match:
                            raise ValueError("Could not determine video resolution")
                        target_w = int(match.group(1))
                        target_h = int(match.group(2))
                    except Exception as e:
                        raise ValueError(f"Failed to read resolution: {e}")
                    
                    processed_paths = []
                    
                    for v_idx, video_path in enumerate(group):
                        if self.is_cancelled:
                            break
                            
                        # Normalize and optionally remove watermark via delogo
                        norm_path = os.path.join(temp_dir, f"norm_{v_idx}.mp4")
                        normalize_video(video_path, norm_path, target_w, target_h, remove_watermark=self.remove_watermark_flag)
                        processed_paths.append(norm_path)
                        
                    if self.is_cancelled:
                        break
                        
                    # Concat
                    out_path = os.path.join(self.output_dir, f"{self.prefix}_{idx:03d}.mp4")
                    concat_videos(processed_paths, out_path, temp_dir, self.remove_sound)
                
                completed += 1
                self.group_done.emit(idx)
            except ffmpeg.Error as e:
                failed += 1
                err_msg = e.stderr.decode('utf8', errors='replace') if e.stderr else str(e)
                self.group_failed.emit(idx, f"FFmpeg Error:\n{err_msg}")
            except Exception as e:
                import traceback
                failed += 1
                self.group_failed.emit(idx, f"Lỗi hệ thống:\n{traceback.format_exc()}")
                
        self.all_done.emit(completed, failed)
