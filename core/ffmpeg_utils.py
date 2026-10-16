import os
import ffmpeg
import imageio_ffmpeg

# (x264 crf, x264 preset) per quality level. Lower crf = higher quality / larger file.
QUALITY_PRESETS = {
    'fast': (23, 'medium'),
    'balanced': (20, 'medium'),
    'high': (17, 'slow'),
}
DEFAULT_QUALITY = 'high'

LOGO_METHODS = ('zoom', 'corner', 'delogo')
DEFAULT_LOGO_METHOD = 'zoom'
# delogo box (bottom-right), as a fraction of the output frame, plus its distance from the edges
DELOGO_W_FRAC, DELOGO_H_FRAC, DELOGO_MARGIN_FRAC = 0.22, 0.10, 0.01

def _delogo_box(width, height):
    """Even-sized bottom-right box that stays >=1px inside the frame (delogo requirement)."""
    margin = max(2, int(width * DELOGO_MARGIN_FRAC))
    w = int(width * DELOGO_W_FRAC) // 2 * 2
    h = int(height * DELOGO_H_FRAC) // 2 * 2
    x = max(1, width - w - margin)
    y = max(1, height - h - margin)
    return x, y, min(w, width - x - 1), min(h, height - y - 1)

def normalize_video(input_path, output_path, target_width, target_height, zoom_percent: int = 20, remove_sound=True, quality: str = DEFAULT_QUALITY, logo_method: str = DEFAULT_LOGO_METHOD):
    # libx264 + yuv420p rejects odd dimensions
    target_width, target_height = target_width // 2 * 2, target_height // 2 * 2
    crf, preset = QUALITY_PRESETS.get(quality, QUALITY_PRESETS[DEFAULT_QUALITY])
    out_kwargs = dict(vcodec='libx264', crf=crf, preset=preset, pix_fmt='yuv420p', movflags='+faststart')
    input_node = ffmpeg.input(input_path)
    video_stream = input_node.video

    zoom_percent = max(0, min(95, zoom_percent))  # defensive clamp; UI enforces 0-90
    if logo_method == 'zoom' and zoom_percent > 0:
        # centered crop, then scale back up
        keep_fraction = 1 - (zoom_percent / 100)
        # round down to even sizes so yuv420p chroma stays aligned
        video_stream = video_stream.filter('crop', f'trunc(iw*{keep_fraction}/2)*2', f'trunc(ih*{keep_fraction}/2)*2')
    elif logo_method == 'corner' and zoom_percent > 0:
        # crop only the right/bottom edges (logo is bottom-right): less upscaling than a centered zoom
        keep_fraction = 1 - (zoom_percent / 100)
        video_stream = video_stream.filter('crop', f'trunc(iw*{keep_fraction}/2)*2', f'trunc(ih*{keep_fraction}/2)*2', 0, 0)

    # lanczos keeps upscaled (zoomed) frames noticeably sharper than the default bicubic
    video_stream = video_stream.filter('scale', target_width, target_height, flags='lanczos')

    if logo_method == 'delogo':
        x, y, w, h = _delogo_box(target_width, target_height)
        video_stream = video_stream.filter('delogo', x=x, y=y, w=w, h=h)

    if remove_sound:
        stream = ffmpeg.output(video_stream, output_path, an=None, **out_kwargs).overwrite_output()
    else:
        ffprobe_exe = imageio_ffmpeg.get_ffmpeg_exe().replace('ffmpeg', 'ffprobe')
        kwargs = {}
        if os.name == 'nt':
            kwargs['creationflags'] = 0x08000000
            
        import subprocess, json
        try:
            res = subprocess.run([ffprobe_exe, '-show_format', '-show_streams', '-of', 'json', input_path], capture_output=True, text=True, **kwargs)
            probe = json.loads(res.stdout)
        except Exception:
            try:
                res = subprocess.run(['ffprobe', '-show_format', '-show_streams', '-of', 'json', input_path], capture_output=True, text=True, **kwargs)
                probe = json.loads(res.stdout)
            except Exception:
                probe = {'streams': []}
            
        has_audio = any(s.get('codec_type') == 'audio' for s in probe.get('streams', []))
        if has_audio:
            stream = ffmpeg.output(video_stream, input_node.audio, output_path, acodec='aac', audio_bitrate='192k', **out_kwargs).overwrite_output()
        else:
            stream = ffmpeg.output(video_stream, output_path, **out_kwargs).overwrite_output()
            
    _run_ffmpeg_quiet(stream, imageio_ffmpeg.get_ffmpeg_exe())

def concat_videos(input_paths, output_path, work_dir, remove_sound=True):
    list_file = os.path.join(work_dir, 'concat_list.txt')
    with open(list_file, 'w', encoding='utf-8') as f:
        for path in input_paths:
            # Escape single quotes in path if needed, though simple paths assumed here
            f.write(f"file '{path}'\n")
    
    stream = ffmpeg.input(list_file, format='concat', safe=0)
    
    if remove_sound:
        stream = stream.video.output(output_path, vcodec='copy', an=None)
    else:
        stream = stream.output(output_path, c='copy')
        
    _run_ffmpeg_quiet(stream, imageio_ffmpeg.get_ffmpeg_exe(), overwrite_output=True)

def _run_ffmpeg_quiet(stream, cmd, overwrite_output=True):
    import subprocess
    args = ffmpeg.compile(stream, cmd=cmd, overwrite_output=overwrite_output)
    kwargs = {}
    if os.name == 'nt':
        kwargs['creationflags'] = 0x08000000
        
    res = subprocess.run(args, capture_output=True, **kwargs)
    if res.returncode != 0:
        raise ffmpeg.Error('ffmpeg', res.stdout, res.stderr)
