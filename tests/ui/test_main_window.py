from ui.main_window import MainWindow

def test_main_window_layout(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    
    assert window.windowTitle() == "VidCat"
    assert window.add_btn.text() == "Thêm video"
    assert window.start_btn.text() == "Bắt đầu"
