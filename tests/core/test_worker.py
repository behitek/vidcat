from core.worker import ProcessingWorker

def test_worker_initialization(qtbot):
    worker = ProcessingWorker([], "out_dir", 2, True, True, "out")
    assert worker.videos == []
    assert worker.is_cancelled == False

def test_worker_groups(qtbot, mocker):
    videos = ["1.mp4", "2.mp4", "3.mp4"]
    worker = ProcessingWorker(videos, "out_dir", 2, False, False, "out")
    
    starts = []
    dones = []
    worker.group_started.connect(starts.append)
    worker.group_done.connect(dones.append)
    
    worker.run()
    
    assert starts == [0, 1]
    assert dones == [0, 1]
