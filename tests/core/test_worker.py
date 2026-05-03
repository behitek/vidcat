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
    mock_cap = mocker.MagicMock()
    mock_cap.get.side_effect = [1280, 720, 1280, 720]
    mocker.patch('cv2.VideoCapture', return_value=mock_cap)
    
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
    mock_remove = mocker.patch('core.worker.remove_watermark')
    mock_concat = mocker.patch('core.worker.concat_videos')
    mock_cap = mocker.MagicMock()
    mock_cap.get.side_effect = [1280, 720]
    mocker.patch('cv2.VideoCapture', return_value=mock_cap)
    
    worker.run()
    
    assert mock_norm.call_count == 2
    assert mock_remove.call_count == 2
    assert mock_concat.call_count == 1
    mock_concat.assert_called_once()
    assert "out_000.mp4" in mock_concat.call_args[0][1]
