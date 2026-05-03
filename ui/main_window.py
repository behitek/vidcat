from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QCheckBox, QSpinBox, QLineEdit, QLabel
from ui.video_list import VideoListWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VidCat")
        self.resize(600, 800)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Input Panel
        self.add_btn = QPushButton("Thêm video")
        self.video_list = VideoListWidget()
        layout.addWidget(self.add_btn)
        layout.addWidget(self.video_list)
        
        # Settings Panel
        self.chk_mute = QCheckBox("Tắt âm thanh")
        self.chk_mute.setChecked(True)
        self.spin_group = QSpinBox()
        self.spin_group.setRange(2, 10)
        self.chk_watermark = QCheckBox("Xóa watermark")
        self.chk_watermark.setChecked(True)
        self.txt_prefix = QLineEdit("output")
        self.lbl_outdir = QLabel("Chưa chọn thư mục")
        self.btn_outdir = QPushButton("Chọn thư mục xuất")
        
        layout.addWidget(self.chk_mute)
        layout.addWidget(self.spin_group)
        layout.addWidget(self.chk_watermark)
        layout.addWidget(self.txt_prefix)
        layout.addWidget(self.lbl_outdir)
        layout.addWidget(self.btn_outdir)
        
        # Progress Panel
        self.lbl_progress = QLabel("Đang chờ...")
        self.start_btn = QPushButton("Bắt đầu")
        self.start_btn.setEnabled(False)
        
        layout.addWidget(self.lbl_progress)
        layout.addWidget(self.start_btn)
