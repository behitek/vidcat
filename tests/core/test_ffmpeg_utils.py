import os
import pytest
from core.ffmpeg_utils import normalize_video, concat_videos, _delogo_box
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
    assert 'crop=trunc(iw*0.8/2)*2:trunc(ih*0.8/2)*2' in ' '.join(args)

def test_normalize_video_zoom_percent(temp_dir, mocker):
    mock_quiet = mocker.patch('core.ffmpeg_utils._run_ffmpeg_quiet')
    mocker.patch('imageio_ffmpeg.get_ffmpeg_exe', return_value='ffmpeg')

    input_path = "input.mp4"
    output_path = os.path.join(temp_dir, "output.mp4")

    normalize_video(input_path, output_path, 1280, 720, zoom_percent=50)

    stream = mock_quiet.call_args[0][0]
    args = ffmpeg.compile(stream, cmd='ffmpeg')
    assert 'crop=trunc(iw*0.5/2)*2:trunc(ih*0.5/2)*2' in ' '.join(args)

def test_normalize_video_zoom_percent_zero_is_noop(temp_dir, mocker):
    mock_quiet = mocker.patch('core.ffmpeg_utils._run_ffmpeg_quiet')
    mocker.patch('imageio_ffmpeg.get_ffmpeg_exe', return_value='ffmpeg')

    input_path = "input.mp4"
    output_path = os.path.join(temp_dir, "output.mp4")

    normalize_video(input_path, output_path, 1280, 720, zoom_percent=0)

    stream = mock_quiet.call_args[0][0]
    args = ffmpeg.compile(stream, cmd='ffmpeg')
    assert 'crop' not in ' '.join(args)

def _compiled(mocker, **kwargs):
    mock_quiet = mocker.patch('core.ffmpeg_utils._run_ffmpeg_quiet')
    normalize_video("input.mp4", "out.mp4", 1280, 720, **kwargs)
    return ' '.join(ffmpeg.compile(mock_quiet.call_args[0][0], cmd='ffmpeg'))

def test_normalize_video_default_is_high_quality(mocker):
    cmd = _compiled(mocker)
    assert 'flags=lanczos' in cmd
    assert '-crf 17' in cmd and '-preset slow' in cmd
    assert '-pix_fmt yuv420p' in cmd and '+faststart' in cmd

@pytest.mark.parametrize("quality,crf", [("fast", 23), ("balanced", 20), ("high", 17), ("bogus", 17)])
def test_normalize_video_quality_levels(mocker, quality, crf):
    assert f'-crf {crf}' in _compiled(mocker, quality=quality)

def test_normalize_video_keeps_audio_with_aac(mocker):
    mocker.patch('core.ffmpeg_utils.imageio_ffmpeg.get_ffmpeg_exe', return_value='ffmpeg')
    mocker.patch('core.ffmpeg_utils.subprocess', create=True)
    import subprocess as sp, json
    fake = mocker.MagicMock(stdout=json.dumps({'streams': [{'codec_type': 'audio'}]}))
    mocker.patch.object(sp, 'run', return_value=fake)
    cmd = _compiled(mocker, remove_sound=False)
    assert '-acodec aac' in cmd and '-b:a 192k' in cmd

def test_corner_crop_keeps_top_left(mocker):
    cmd = _compiled(mocker, zoom_percent=10, logo_method='corner')
    assert 'crop=trunc(iw*0.9/2)*2:trunc(ih*0.9/2)*2:0:0' in cmd
    assert 'delogo' not in cmd

def test_corner_crop_zero_is_noop(mocker):
    assert 'crop' not in _compiled(mocker, zoom_percent=0, logo_method='corner')

def test_delogo_bottom_right_after_scale(mocker):
    cmd = _compiled(mocker, logo_method='delogo')
    assert 'crop' not in cmd
    assert cmd.index('scale=') < cmd.index('delogo=')
    x, y, w, h = _delogo_box(1280, 720)
    assert f'delogo=h={h}:w={w}:x={x}:y={y}' in cmd  # ffmpeg-python sorts kwargs

@pytest.mark.parametrize("size", [(1920, 1080), (1280, 720), (720, 1280), (640, 360), (320, 240)])
def test_delogo_box_inside_frame_bottom_right(size):
    W, H = size
    x, y, w, h = _delogo_box(W, H)
    assert x >= 1 and y >= 1 and w > 0 and h > 0
    assert x + w <= W - 1 and y + h <= H - 1
    assert x > W / 2 and y > H / 2

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
