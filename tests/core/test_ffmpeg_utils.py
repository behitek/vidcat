import os
import pytest
from core.ffmpeg_utils import normalize_video
import ffmpeg

def test_normalize_video(temp_dir, mocker):
    mock_run = mocker.patch('ffmpeg.run')
    mock_input = mocker.patch('ffmpeg.input')
    
    input_path = "input.mp4"
    output_path = os.path.join(temp_dir, "output.mp4")
    
    normalize_video(input_path, output_path, 1280, 720)
    
    mock_input.assert_called_once_with(input_path)
    assert mock_run.called
