import os
import tempfile
import shutil
import ffmpeg
import subprocess
import re
import imageio_ffmpeg
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt6.QtCore import QThread, pyqtSignal
from core.ffmpeg_utils import normalize_video, concat_videos
from core.grouping import group_videos_by_suffix, sanitize_suffix, dedupe_suffixes

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
    
    def __init__(self, videos, output_dir, zoom_percent, remove_sound, prefix, n_parallel=1):
        super().__init__()
        self.videos = videos
        self.output_dir = output_dir
        self.zoom_percent = zoom_percent
        self.remove_sound = remove_sound
        self.prefix = prefix
        self.n_parallel = n_parallel
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True

    def process_group(self, idx, group, output_name):
        if self.is_cancelled:
            return idx, False, "Cancelled"
            
        self.group_started.emit(idx)
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # 1. Get target resolution from first video using ffmpeg
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                try:
                    kwargs = {}
                    if os.name == 'nt':
                        kwargs['creationflags'] = 0x08000000
                    result = subprocess.run([ffmpeg_exe, "-i", group.paths[0]], stderr=subprocess.PIPE, text=True, **kwargs)
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
                
                for v_idx, video_path in enumerate(group.paths):
                    if self.is_cancelled:
                        return idx, False, "Cancelled"

                    # Normalize and zoom-crop to remove watermark
                    norm_path = os.path.join(temp_dir, f"norm_{v_idx}.mp4")
                    normalize_video(video_path, norm_path, target_w, target_h, zoom_percent=self.zoom_percent, remove_sound=self.remove_sound)
                    processed_paths.append(norm_path)

                if self.is_cancelled:
                    return idx, False, "Cancelled"

                # Concat
                out_path = os.path.join(self.output_dir, f"{self.prefix}_{output_name}.mp4")
                concat_videos(processed_paths, out_path, temp_dir, self.remove_sound)
            return idx, True, None
        except ffmpeg.Error as e:
            err_msg = e.stderr.decode('utf8', errors='replace') if e.stderr else str(e)
            return idx, False, f"FFmpeg Error:\n{err_msg}"
        except Exception as e:
            import traceback
            return idx, False, f"Lỗi hệ thống:\n{traceback.format_exc()}"

    def run(self):
        groups = group_videos_by_suffix(self.videos)
        output_names = dedupe_suffixes([sanitize_suffix(g.suffix) for g in groups])
        completed = 0
        failed = 0

        with ThreadPoolExecutor(max_workers=self.n_parallel) as executor:
            futures = [executor.submit(self.process_group, idx, group, output_names[idx]) for idx, group in enumerate(groups)]
            
            for future in as_completed(futures):
                if self.is_cancelled:
                    break
                    
                idx, success, error_msg = future.result()
                if error_msg == "Cancelled":
                    continue
                    
                if success:
                    completed += 1
                    self.group_done.emit(idx)
                else:
                    failed += 1
                    self.group_failed.emit(idx, error_msg)
                    
        self.all_done.emit(completed, failed)
