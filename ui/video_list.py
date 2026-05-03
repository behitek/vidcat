import os
from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt

class VideoListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        
    def add_video(self, file_path):
        filename = os.path.basename(file_path)
        item = QListWidgetItem(filename)
        item.setData(100, file_path) # Custom role for full path
        self.addItem(item)
        
    def get_videos(self):
        return [self.item(i).data(100) for i in range(self.count())]
