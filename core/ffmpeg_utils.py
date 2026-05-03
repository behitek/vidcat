import os
import ffmpeg

def normalize_video(input_path, output_path, target_width, target_height):
    stream = (
        ffmpeg
        .input(input_path)
        .filter('scale', target_width, target_height)
        .output(output_path)
        .overwrite_output()
    )
    ffmpeg.run(stream, quiet=True)

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
        
    ffmpeg.run(stream, overwrite_output=True, quiet=True)
