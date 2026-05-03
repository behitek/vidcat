from ui.video_list import VideoListWidget
from PyQt6.QtWidgets import QListWidgetItem

def test_video_list_widget(qtbot):
    widget = VideoListWidget()
    qtbot.addWidget(widget)
    
    widget.add_video("test.mp4")
    assert widget.count() == 1
    
    item = widget.item(0)
    assert item.data(100) == "test.mp4" # Role 100 for path
