import datetime
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QCheckBox, QSpinBox, QLineEdit, QLabel, QFileDialog, QTextEdit, QApplication
from ui.video_list import VideoListWidget
from core.worker import ProcessingWorker

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
        
        # Log Panel
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.btn_copy_log = QPushButton("Sao chép nhật ký")
        self.btn_copy_log.clicked.connect(self.on_copy_log)
        
        layout.addWidget(QLabel("Nhật ký (Logs):"))
        layout.addWidget(self.txt_log)
        layout.addWidget(self.btn_copy_log)
        
        self.btn_outdir.clicked.connect(self.on_browse_outdir)
        self.add_btn.clicked.connect(self.on_add_video)
        self.start_btn.clicked.connect(self.on_start)
        self.worker = None
        
    def on_browse_outdir(self):
        directory = QFileDialog.getExistingDirectory(self, "Chọn thư mục xuất")
        if directory:
            self.lbl_outdir.setText(directory)
            self.start_btn.setEnabled(True)
            
    def on_add_video(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Chọn video", "", "Video files (*.mp4 *.mov *.avi *.mkv)")
        if files:
            for f in files:
                self.video_list.add_video(f)

    def log_message(self, msg):
        tz = datetime.timezone(datetime.timedelta(hours=7))
        now = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        self.txt_log.append(f"[{now}] {msg}")

    def on_copy_log(self):
        QApplication.clipboard().setText(self.txt_log.toPlainText())

    def on_start(self):
        if self.worker is not None and self.worker.isRunning():
            self.worker.cancel()
            self.start_btn.setEnabled(False)
            self.lbl_progress.setText("Đang hủy...")
            self.log_message("Người dùng yêu cầu hủy...")
            return
            
        videos = self.video_list.get_videos()
        if not videos:
            return
            
        self.txt_log.clear()
        self.log_message(f"Bắt đầu xử lý {len(videos)} video...")
        
        self.start_btn.setText("Hủy")
        self.add_btn.setEnabled(False)
        self.worker = ProcessingWorker(
            videos=videos,
            output_dir=self.lbl_outdir.text(),
            group_size=self.spin_group.value(),
            remove_watermark_flag=self.chk_watermark.isChecked(),
            remove_sound=self.chk_mute.isChecked(),
            prefix=self.txt_prefix.text()
        )
        self.worker.group_started.connect(lambda idx: self.lbl_progress.setText(f"Đang xử lý nhóm {idx + 1}..."))
        self.worker.group_failed.connect(lambda idx, err: self.log_message(f"LỖI Nhóm {idx + 1}:\n{err}"))
        self.worker.all_done.connect(self.on_all_done)
        self.worker.start()
        
    def on_all_done(self, completed, failed):
        msg = f"Hoàn thành: {completed} thành công, {failed} lỗi"
        self.lbl_progress.setText(msg)
        self.log_message(msg)
        self.start_btn.setText("Bắt đầu")
        self.start_btn.setEnabled(True)
        self.add_btn.setEnabled(True)
