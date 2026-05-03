from ui.main_window import MainWindow
from unittest.mock import patch

def test_main_window_layout(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    
    assert window.windowTitle() == "VidCat"
    assert window.add_btn.text() == "Thêm video"
    assert window.start_btn.text() == "Bắt đầu"

def test_browse_output_dir(qtbot, mocker):
    window = MainWindow()
    qtbot.addWidget(window)
    
    mock_dialog = mocker.patch('PyQt6.QtWidgets.QFileDialog.getExistingDirectory', return_value='/fake/out')
    window.btn_outdir.click()
    
    assert window.lbl_outdir.text() == '/fake/out'
    assert window.start_btn.isEnabled() == True

def test_add_video(qtbot, mocker):
    window = MainWindow()
    qtbot.addWidget(window)
    
    mock_dialog = mocker.patch('PyQt6.QtWidgets.QFileDialog.getOpenFileNames', return_value=(['/fake/v1.mp4', '/fake/v2.mp4'], ''))
    window.add_btn.click()
    
    assert window.video_list.count() == 2

def test_start_worker(qtbot, mocker):
    window = MainWindow()
    qtbot.addWidget(window)
    
    window.video_list.add_video("1.mp4")
    window.video_list.add_video("2.mp4")
    window.lbl_outdir.setText("out_dir")
    
    mock_start = mocker.patch('core.worker.ProcessingWorker.start')
    
    window.on_start()
    
    assert window.worker is not None
    assert mock_start.called
    assert window.start_btn.text() == "Hủy"
