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
