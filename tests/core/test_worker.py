from core.worker import ProcessingWorker

def test_worker_initialization(qtbot):
    worker = ProcessingWorker([], "out_dir", 2, True, True, "out")
    assert worker.videos == []
    assert worker.is_cancelled == False

def test_worker_groups(qtbot, mocker):
    videos = ["1.mp4", "2.mp4", "3.mp4"]
    worker = ProcessingWorker(videos, "out_dir", 2, False, False, "out")
    
    mocker.patch('core.worker.normalize_video')
    mocker.patch('core.worker.concat_videos')
    mocker.patch('ffmpeg.probe', return_value={'streams': [{'codec_type': 'video', 'width': 1280, 'height': 720}]})
    
    starts = []
    dones = []
    worker.group_started.connect(starts.append)
    worker.group_done.connect(dones.append)
    
    worker.run()
    
    assert starts == [0, 1]
    assert dones == [0, 1]

def test_worker_pipeline(qtbot, mocker):
    videos = ["1.mp4", "2.mp4"]
    worker = ProcessingWorker(videos, "out_dir", 2, True, True, "out")
    
    mock_norm = mocker.patch('core.worker.normalize_video')
    mock_concat = mocker.patch('core.worker.concat_videos')
    mocker.patch('ffmpeg.probe', return_value={'streams': [{'codec_type': 'video', 'width': 1280, 'height': 720}]})
    
    worker.run()
    
    assert mock_norm.call_count == 2
    assert mock_concat.call_count == 1
    mock_concat.assert_called_once()
    assert "out_000.mp4" in mock_concat.call_args[0][1]
