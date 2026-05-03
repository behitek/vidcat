import os
import pytest
from core.ffmpeg_utils import normalize_video, concat_videos
import ffmpeg

def test_normalize_video(temp_dir, mocker):
    mock_run = mocker.patch('ffmpeg.run')
    mock_input = mocker.patch('ffmpeg.input')
    
    input_path = "input.mp4"
    output_path = os.path.join(temp_dir, "output.mp4")
    
    normalize_video(input_path, output_path, 1280, 720)
    
    mock_input.assert_called_once_with(input_path)
    assert mock_run.called

def test_normalize_video_with_watermark_removal(temp_dir, mocker):
    mock_run = mocker.patch('ffmpeg.run')
    mock_input = mocker.patch('ffmpeg.input')
    
    input_path = "input.mp4"
    output_path = os.path.join(temp_dir, "output.mp4")
    
    normalize_video(input_path, output_path, 1280, 720, remove_watermark=True)
    
    mock_input.assert_called_once_with(input_path)
    assert mock_run.called

def test_concat_videos(temp_dir, mocker):
    mock_run = mocker.patch('ffmpeg.run')
    mock_input = mocker.patch('ffmpeg.input')
    
    inputs = ["v1.mp4", "v2.mp4"]
    out_path = os.path.join(temp_dir, "out.mp4")
    
    concat_videos(inputs, out_path, temp_dir, remove_sound=True)
    
    list_file = os.path.join(temp_dir, 'concat_list.txt')
    assert os.path.exists(list_file)
    with open(list_file, 'r') as f:
        content = f.read()
        assert "file 'v1.mp4'" in content
        assert "file 'v2.mp4'" in content
        
    mock_input.assert_called_once_with(list_file, format='concat', safe=0)
    assert mock_run.called
