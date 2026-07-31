import os
import ffmpeg
import imageio_ffmpeg

def normalize_video(input_path, output_path, target_width, target_height, zoom_percent: int = 20, remove_sound=True):
    input_node = ffmpeg.input(input_path)
    video_stream = input_node.video

    zoom_percent = max(0, min(95, zoom_percent))  # defensive clamp; UI enforces 0-90
    if zoom_percent > 0:
        keep_fraction = 1 - (zoom_percent / 100)
        video_stream = video_stream.filter('crop', f'iw*{keep_fraction}', f'ih*{keep_fraction}')

    video_stream = video_stream.filter('scale', target_width, target_height)

    if remove_sound:
        stream = ffmpeg.output(video_stream, output_path, an=None).overwrite_output()
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
            stream = ffmpeg.output(video_stream, input_node.audio, output_path).overwrite_output()
        else:
            stream = ffmpeg.output(video_stream, output_path).overwrite_output()
            
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
