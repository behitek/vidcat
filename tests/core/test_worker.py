from core.worker import ProcessingWorker

def test_worker_initialization(qtbot):
    worker = ProcessingWorker([], "out_dir", 20, True, "out")
    assert worker.videos == []
    assert worker.zoom_percent == 20
    assert worker.is_cancelled == False
    assert not hasattr(worker, "group_size")
    assert not hasattr(worker, "watermark_method")

def _mock_ffmpeg(mocker):
    mocker.patch('core.worker.normalize_video')
    mocker.patch('core.worker.concat_videos')
    mocker.patch('imageio_ffmpeg.get_ffmpeg_exe', return_value='ffmpeg')
    mock_run = mocker.MagicMock()
    mock_run.stderr = "Stream #0:0: Video: h264, yuv420p, 1280x720, 30 fps"
    mocker.patch('subprocess.run', return_value=mock_run)

def test_worker_groups_by_suffix(qtbot, mocker):
    # 01_A / 02_A share suffix "A" -> one group; 01_B is its own group.
    videos = ["01_A.mp4", "02_A.mp4", "01_B.mp4"]
    worker = ProcessingWorker(videos, "out_dir", 20, False, "out")

    _mock_ffmpeg(mocker)

    # group_done is emitted from run() on the calling thread, so it's safe to
    # assert synchronously here. group_started is emitted from inside
    # process_group() on a ThreadPoolExecutor worker thread and needs an
    # event-loop pump to be delivered to a cross-thread receiver, so it isn't
    # asserted in this synchronous test (pre-existing characteristic of
    # QThread + ThreadPoolExecutor, not specific to this change).
    dones = []
    worker.group_done.connect(dones.append)

    worker.run()

    assert dones == [0, 1]

def test_worker_groups_unmatched_filenames_are_singleton(qtbot, mocker):
    videos = ["1.mp4", "2.mp4"]
    worker = ProcessingWorker(videos, "out_dir", 20, False, "out")

    _mock_ffmpeg(mocker)

    dones = []
    worker.group_done.connect(dones.append)

    worker.run()

    # neither filename matches <order>_<suffix>, so each becomes its own group
    assert dones == [0, 1]

def test_worker_pipeline_output_named_by_suffix(qtbot, mocker):
    videos = ["01_A.mp4", "02_A.mp4"]
    worker = ProcessingWorker(videos, "out_dir", 20, True, "out")

    mock_norm = mocker.patch('core.worker.normalize_video')
    mock_concat = mocker.patch('core.worker.concat_videos')
    mocker.patch('imageio_ffmpeg.get_ffmpeg_exe', return_value='ffmpeg')
    mock_run = mocker.MagicMock()
    mock_run.stderr = "Stream #0:0: Video: h264, yuv420p, 1280x720, 30 fps"
    mocker.patch('subprocess.run', return_value=mock_run)

    worker.run()

    assert mock_norm.call_count == 2
    assert mock_norm.call_args_list[0].kwargs['zoom_percent'] == 20
    assert mock_concat.call_count == 1
    mock_concat.assert_called_once()
    assert "out_A.mp4" in mock_concat.call_args[0][1]

def test_worker_zoom_percent_zero_passed_through(qtbot, mocker):
    videos = ["01_A.mp4", "02_A.mp4"]
    worker = ProcessingWorker(videos, "out_dir", 0, True, "out")

    mock_norm = mocker.patch('core.worker.normalize_video')
    mocker.patch('core.worker.concat_videos')
    mocker.patch('imageio_ffmpeg.get_ffmpeg_exe', return_value='ffmpeg')
    mock_run = mocker.MagicMock()
    mock_run.stderr = "Stream #0:0: Video: h264, yuv420p, 1280x720, 30 fps"
    mocker.patch('subprocess.run', return_value=mock_run)

    worker.run()

    assert mock_norm.call_args_list[0].kwargs['zoom_percent'] == 0
