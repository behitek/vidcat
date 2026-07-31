import os
import pytest
from core.ffmpeg_utils import normalize_video, concat_videos
import ffmpeg

def test_normalize_video(temp_dir, mocker):
    mock_quiet = mocker.patch('core.ffmpeg_utils._run_ffmpeg_quiet')
    mocker.patch('imageio_ffmpeg.get_ffmpeg_exe', return_value='ffmpeg')

    input_path = "input.mp4"
    output_path = os.path.join(temp_dir, "output.mp4")

    normalize_video(input_path, output_path, 1280, 720)

    assert mock_quiet.called
    stream = mock_quiet.call_args[0][0]
    args = ffmpeg.compile(stream, cmd='ffmpeg')
    assert 'crop=iw*0.8:ih*0.8' in ' '.join(args)

def test_normalize_video_zoom_percent(temp_dir, mocker):
    mock_quiet = mocker.patch('core.ffmpeg_utils._run_ffmpeg_quiet')
    mocker.patch('imageio_ffmpeg.get_ffmpeg_exe', return_value='ffmpeg')

    input_path = "input.mp4"
    output_path = os.path.join(temp_dir, "output.mp4")

    normalize_video(input_path, output_path, 1280, 720, zoom_percent=50)

    stream = mock_quiet.call_args[0][0]
    args = ffmpeg.compile(stream, cmd='ffmpeg')
    assert 'crop=iw*0.5:ih*0.5' in ' '.join(args)

def test_normalize_video_zoom_percent_zero_is_noop(temp_dir, mocker):
    mock_quiet = mocker.patch('core.ffmpeg_utils._run_ffmpeg_quiet')
    mocker.patch('imageio_ffmpeg.get_ffmpeg_exe', return_value='ffmpeg')

    input_path = "input.mp4"
    output_path = os.path.join(temp_dir, "output.mp4")

    normalize_video(input_path, output_path, 1280, 720, zoom_percent=0)

    stream = mock_quiet.call_args[0][0]
    args = ffmpeg.compile(stream, cmd='ffmpeg')
    assert 'crop' not in ' '.join(args)

def test_concat_videos(temp_dir, mocker):
    mock_quiet = mocker.patch('core.ffmpeg_utils._run_ffmpeg_quiet')
    mocker.patch('imageio_ffmpeg.get_ffmpeg_exe', return_value='ffmpeg')

    inputs = ["v1.mp4", "v2.mp4"]
    out_path = os.path.join(temp_dir, "out.mp4")

    concat_videos(inputs, out_path, temp_dir, remove_sound=True)

    list_file = os.path.join(temp_dir, 'concat_list.txt')
    assert os.path.exists(list_file)
    with open(list_file, 'r') as f:
        content = f.read()
        assert "file 'v1.mp4'" in content
        assert "file 'v2.mp4'" in content

    assert mock_quiet.called
