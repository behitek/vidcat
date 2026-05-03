from core.worker import ProcessingWorker

def test_worker_initialization(qtbot):
    worker = ProcessingWorker([], "out_dir", 2, True, True, "out")
    assert worker.videos == []
    assert worker.is_cancelled == False
