import datetime
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox, QComboBox, QSpinBox, QLineEdit, QLabel, QFileDialog, QTextEdit, QApplication, QSystemTrayIcon, QMenu, QStyle
from PyQt6.QtGui import QColor, QDesktopServices, QAction, QIcon
from PyQt6.QtCore import QUrl, QEvent, QSettings
from ui.video_list import VideoListWidget
from core.worker import ProcessingWorker
from core.grouping import group_videos_by_suffix
from core.ffmpeg_utils import DEFAULT_QUALITY, DEFAULT_LOGO_METHOD

QUALITY_LABELS = [
    ("fast", "Nhanh (file nhỏ)"),
    ("balanced", "Cân bằng"),
    ("high", "Cao (khuyến nghị)"),
]

# (key, combo label, spinbox label or None if no spinbox, default %)
LOGO_METHOD_OPTIONS = [
    ("none", "Không xóa logo", None, 0),
    ("zoom", "Zoom-in (cắt đều 4 cạnh)", "% zoom:", 20),
    ("corner", "Cắt góc phải-dưới", "% cắt cạnh phải/dưới:", 10),
    ("delogo", "Làm mờ logo (giữ nguyên khung hình)", None, 0),
]

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VidCat")
        self.resize(600, 800)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Settings object
        self.settings = QSettings("VidcatDev", "Vidcat")
        
        # Input Panel
        input_btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Thêm video (chọn nhiều)")
        self.clear_btn = QPushButton("Xóa danh sách")
        
        self.info_btn = QPushButton()
        self.info_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation))
        self.info_btn.setToolTip("Hướng dẫn sử dụng")
        self.info_btn.clicked.connect(self.show_guide)
        
        input_btn_layout.addWidget(self.add_btn)
        input_btn_layout.addWidget(self.clear_btn)
        input_btn_layout.addStretch()
        input_btn_layout.addWidget(self.info_btn)
        
        self.video_list = VideoListWidget()
        layout.addLayout(input_btn_layout)
        layout.addWidget(self.video_list)
        
        # Settings Panel
        self.chk_mute = QCheckBox("Tắt âm thanh")
        self.chk_mute.setChecked(True)
        
        parallel_layout = QHBoxLayout()
        parallel_layout.addWidget(QLabel("Số luồng xử lý đồng thời:"))
        self.spin_parallel = QSpinBox()
        max_parallel = self.get_max_parallel_tasks()
        self.spin_parallel.setRange(1, max_parallel)
        parallel_layout.addWidget(self.spin_parallel)
        
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Xóa logo (góc phải-dưới):"))
        self.cmb_logo_method = QComboBox()
        for key, label, _, _ in LOGO_METHOD_OPTIONS:
            self.cmb_logo_method.addItem(label, key)
        zoom_layout.addWidget(self.cmb_logo_method)
        self.lbl_zoom = QLabel()
        zoom_layout.addWidget(self.lbl_zoom)
        self.spin_zoom_percent = QSpinBox()
        self.spin_zoom_percent.setRange(0, 90)
        self.spin_zoom_percent.setSuffix("%")
        zoom_layout.addWidget(self.spin_zoom_percent)
        self._logo_pct = {key: default for key, _, _, default in LOGO_METHOD_OPTIONS}
        self._logo_key = DEFAULT_LOGO_METHOD
        self.cmb_logo_method.currentIndexChanged.connect(self.on_logo_method_changed)
        
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Chất lượng video:"))
        self.cmb_quality = QComboBox()
        for key, label in QUALITY_LABELS:
            self.cmb_quality.addItem(label, key)
        quality_layout.addWidget(self.cmb_quality)

        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel("Tiền tố tên file:"))
        self.txt_prefix = QLineEdit("output")
        prefix_layout.addWidget(self.txt_prefix)
        
        self.lbl_outdir = QLabel("Chưa chọn thư mục")
        self.btn_outdir = QPushButton("Chọn thư mục xuất")
        
        self.chk_tray = QCheckBox("Chạy ngầm (Ẩn xuống System Tray)")
        self.chk_tray.setChecked(False)
        self.chk_tray.toggled.connect(self.on_tray_toggled)
        
        layout.addWidget(self.chk_mute)
        layout.addLayout(parallel_layout)
        layout.addLayout(zoom_layout)
        layout.addLayout(quality_layout)
        layout.addLayout(prefix_layout)
        layout.addWidget(self.lbl_outdir)
        layout.addWidget(self.btn_outdir)
        layout.addWidget(self.chk_tray)
        
        # Progress Panel
        self.lbl_progress = QLabel("Đang chờ...")
        self.lbl_progress.setWordWrap(True)
        
        self.start_btn = QPushButton("Bắt đầu")
        self.start_btn.setEnabled(False)
        
        layout.addWidget(self.lbl_progress)
        layout.addWidget(self.start_btn)
        
        from PyQt6.QtCore import QTimer, Qt
        self.lbl_progress.setTextFormat(Qt.TextFormat.RichText)
        self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_idx = 0
        self.spinner_timer = QTimer(self)
        self.spinner_timer.timeout.connect(self.on_spinner_timer)
        self.group_statuses = []
        self.final_message = ""
        
        # Log Panel
        self.btn_toggle_log = QPushButton("Hiện nhật ký ▼")
        self.btn_toggle_log.setCheckable(True)
        self.btn_toggle_log.clicked.connect(self.on_toggle_log)
        
        self.log_widget = QWidget()
        log_layout = QVBoxLayout(self.log_widget)
        log_layout.setContentsMargins(0, 0, 0, 0)
        
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.btn_copy_log = QPushButton("Sao chép nhật ký")
        self.btn_copy_log.clicked.connect(self.on_copy_log)
        
        log_layout.addWidget(self.txt_log)
        log_layout.addWidget(self.btn_copy_log)
        
        self.log_widget.setVisible(False)
        
        layout.addWidget(self.btn_toggle_log)
        layout.addWidget(self.log_widget)
        
        self.btn_outdir.clicked.connect(self.on_browse_outdir)
        self.add_btn.clicked.connect(self.on_add_video)
        self.clear_btn.clicked.connect(self.video_list.clear)
        self.start_btn.clicked.connect(self.on_start)
        self.worker = None
        self.start_time = None
        
        self.video_list.model().rowsInserted.connect(lambda parent, first, last: self.update_video_groups())
        self.video_list.model().rowsRemoved.connect(lambda parent, first, last: self.update_video_groups())
        self.video_list.model().rowsMoved.connect(lambda parent, start, end, destination, row: self.update_video_groups())
        self.video_list.model().layoutChanged.connect(self.update_video_groups)
        self.lbl_progress.linkActivated.connect(self.on_progress_link_activated)

        # Tray Icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QApplication.instance().windowIcon())
        
        tray_menu = QMenu()
        show_action = QAction("Hiển thị VidCat", self)
        show_action.triggered.connect(self.show_window)
        quit_action = QAction("Thoát", self)
        quit_action.triggered.connect(self.quit_app)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        self.load_settings()

    def get_max_parallel_tasks(self):
        import os, ctypes
        try:
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ('dwLength', ctypes.c_ulong),
                    ('dwMemoryLoad', ctypes.c_ulong),
                    ('ullTotalPhys', ctypes.c_ulonglong),
                    ('ullAvailPhys', ctypes.c_ulonglong),
                    ('ullTotalPageFile', ctypes.c_ulonglong),
                    ('ullAvailPageFile', ctypes.c_ulonglong),
                    ('ullTotalVirtual', ctypes.c_ulonglong),
                    ('ullAvailVirtual', ctypes.c_ulonglong),
                    ('sullAvailExtendedVirtual', ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(stat)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            ram_gb = stat.ullTotalPhys / (1024**3)
            # Ffmpeg takes some RAM, ~1.5GB per task.
            ram_max = max(1, int(ram_gb / 1.5))
        except Exception:
            ram_max = 4
            
        cpu_count = os.cpu_count() or 4
        cpu_max = max(1, cpu_count - 1) # leave 1 core for OS
        
        return min(cpu_max, ram_max)

    def on_tray_toggled(self, checked):
        QApplication.instance().setQuitOnLastWindowClosed(not checked)
        if checked:
            self.tray_icon.show()
        else:
            self.tray_icon.hide()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger or reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()

    def show_window(self):
        self.show()
        self.activateWindow()
        self.showNormal()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized() and self.chk_tray.isChecked():
                self.hide()
                self.tray_icon.showMessage("VidCat", "Ứng dụng đang chạy ngầm", QSystemTrayIcon.MessageIcon.Information, 2000)
        super().changeEvent(event)

    def closeEvent(self, event):
        self.save_settings()
        if self.chk_tray.isChecked():
            self.hide()
            self.tray_icon.showMessage("VidCat", "Ứng dụng đang chạy ngầm", QSystemTrayIcon.MessageIcon.Information, 2000)
            event.ignore()
        else:
            event.accept()

    def quit_app(self):
        self.save_settings()
        QApplication.instance().quit()

    def on_logo_method_changed(self, _=None):
        self._logo_pct[self._logo_key] = self.spin_zoom_percent.value()
        self._logo_key = self.cmb_logo_method.currentData()
        self._refresh_logo_controls()

    def _refresh_logo_controls(self):
        _, _, label, _ = next(o for o in LOGO_METHOD_OPTIONS if o[0] == self._logo_key)
        self.lbl_zoom.setVisible(label is not None)
        self.spin_zoom_percent.setVisible(label is not None)
        if label is not None:
            self.lbl_zoom.setText(label)
            self.spin_zoom_percent.setValue(self._logo_pct[self._logo_key])

    def load_settings(self):
        import os
        self.chk_mute.setChecked(self.settings.value("mute", True, type=bool))
        self.spin_parallel.setValue(self.settings.value("parallel", min(2, self.spin_parallel.maximum()), type=int))
        for key, _, _, default in LOGO_METHOD_OPTIONS:
            # "zoom_percent" is the legacy key from before logo methods existed
            legacy = "zoom_percent" if key == "zoom" else f"logo_pct_{key}"
            self._logo_pct[key] = self.settings.value(f"logo_pct_{key}", self.settings.value(legacy, default, type=int), type=int)
        idx = self.cmb_logo_method.findData(self.settings.value("logo_method", DEFAULT_LOGO_METHOD, type=str))
        self.cmb_logo_method.blockSignals(True)
        self.cmb_logo_method.setCurrentIndex(max(idx, 0))
        self.cmb_logo_method.blockSignals(False)
        self._logo_key = self.cmb_logo_method.currentData()
        self._refresh_logo_controls()
        idx = self.cmb_quality.findData(self.settings.value("quality", DEFAULT_QUALITY, type=str))
        self.cmb_quality.setCurrentIndex(idx if idx >= 0 else self.cmb_quality.findData(DEFAULT_QUALITY))
        self.txt_prefix.setText(self.settings.value("prefix", "output", type=str))
        
        outdir = self.settings.value("outdir", "Chưa chọn thư mục", type=str)
        if outdir and outdir != "Chưa chọn thư mục" and os.path.exists(outdir):
            self.lbl_outdir.setText(outdir)
            self.start_btn.setEnabled(True)
            
        self.chk_tray.setChecked(self.settings.value("tray", False, type=bool))

    def save_settings(self):
        self.settings.setValue("mute", self.chk_mute.isChecked())
        self.settings.setValue("parallel", self.spin_parallel.value())
        self._logo_pct[self._logo_key] = self.spin_zoom_percent.value()
        for key, pct in self._logo_pct.items():
            self.settings.setValue(f"logo_pct_{key}", pct)
        self.settings.setValue("logo_method", self.cmb_logo_method.currentData())
        self.settings.setValue("quality", self.cmb_quality.currentData())
        self.settings.setValue("prefix", self.txt_prefix.text())
        self.settings.setValue("outdir", self.lbl_outdir.text())
        self.settings.setValue("tray", self.chk_tray.isChecked())

    def show_guide(self):
        from PyQt6.QtWidgets import QMessageBox
        from PyQt6.QtCore import Qt
        guide_text = """<h3>Hướng dẫn sử dụng VidCat</h3>
<p><b>1. Thêm video:</b> Bấm "Thêm video" để chọn danh sách các video cần xử lý.</p>
<p><b>2. Cấu hình:</b>
<ul>
<li><b>Nhóm video:</b> Tên file được tách theo dấu "_", phần đầu là số thứ tự, phần thứ hai là tên nhóm (các phần sau dấu "_" tiếp theo không ảnh hưởng đến việc nhóm). Ví dụ: 01_A.mp4, 02_A_bonus.mp4 đều thuộc nhóm "A" và được ghép theo đúng thứ tự số. Video không đúng định dạng này sẽ tự thành một nhóm riêng.</li>
<li><b>Số luồng xử lý đồng thời:</b> Cho phép xử lý nhiều nhóm cùng lúc để tăng tốc độ. Số lượng tối đa phụ thuộc vào CPU/RAM của máy.</li>
<li><b>Xóa logo (Zoom-in):</b> Cắt bỏ một tỉ lệ % viền ngoài của video để loại bỏ logo ở các góc. Chỉnh tỉ lệ % theo nhu cầu (0% = không cắt).</li>
<li><b>Chạy ngầm:</b> Nếu tích chọn, khi thu nhỏ hoặc đóng, app sẽ chạy ẩn dưới System Tray.</li>
</ul></p>
<p><b>3. Xuất file:</b> Bấm "Chọn thư mục xuất" rồi nhấn "Bắt đầu". Các video sẽ tự động được xử lý.</p>
<hr>
<p><b>Thông tin & Hỗ trợ</b></p>
<p>Phiên bản: 1.0.0<br>
Tác giả: Hieu Nguyen<br>
Liên hệ hỗ trợ: <a href="https://behitek.com/contact">behitek.com/contact</a></p>
"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Hướng dẫn sử dụng")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        msg.setText(guide_text)
        msg.exec()

    def update_video_groups(self):
        import os
        videos = self.video_list.get_videos()
        groups = group_videos_by_suffix(videos)

        # Flatten groups back into a row order where same-group videos sit
        # next to each other, in group-first-appearance / in-group order.
        ordered = [(it.index, group_idx, group.suffix)
                   for group_idx, group in enumerate(groups)
                   for it in group.items]
        ordered_indices = [entry[0] for entry in ordered]

        if ordered_indices != list(range(len(videos))):
            model = self.video_list.model()
            self.video_list.blockSignals(True)
            model.blockSignals(True)
            try:
                items = [self.video_list.takeItem(0) for _ in range(self.video_list.count())]
                for new_pos, orig_idx in enumerate(ordered_indices):
                    self.video_list.insertItem(new_pos, items[orig_idx])
            finally:
                model.blockSignals(False)
                self.video_list.blockSignals(False)

        colors = [QColor("#e6f7ff"), QColor("#f6ffed"), QColor("#fff1f0"), QColor("#f9f0ff"), QColor("#fff7e6")]
        for new_pos, (orig_idx, group_idx, suffix) in enumerate(ordered):
            item = self.video_list.item(new_pos)
            item.setBackground(colors[group_idx % len(colors)])

            # Add group tag text to filename
            file_path = item.data(100)
            if file_path:
                filename = os.path.basename(file_path)
                item.setText(f"[Nhóm: {suffix}] {filename}")

    def on_progress_link_activated(self, link):
        import os
        if os.path.exists(link):
            QDesktopServices.openUrl(QUrl.fromLocalFile(link))
        elif link == "open_dir":
            outdir = self.lbl_outdir.text()
            if os.path.exists(outdir):
                QDesktopServices.openUrl(QUrl.fromLocalFile(outdir))
        
    def on_browse_outdir(self):
        directory = QFileDialog.getExistingDirectory(self, "Chọn thư mục xuất")
        if directory:
            self.lbl_outdir.setText(directory)
            self.start_btn.setEnabled(True)
            
    def on_add_video(self):
        import os
        downloads_dir = os.path.expanduser("~/Downloads")
        files, _ = QFileDialog.getOpenFileNames(self, "Chọn video", downloads_dir, "Video files (*.mp4 *.mov *.avi *.mkv)")
        if files:
            for f in files:
                self.video_list.add_video(f)

    def log_message(self, msg):
        tz = datetime.timezone(datetime.timedelta(hours=7))
        now = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        self.txt_log.append(f"[{now}] {msg}")
        
        if "LỖI" in msg and not self.btn_toggle_log.isChecked():
            self.btn_toggle_log.setChecked(True)
            self.on_toggle_log(True)

    def on_toggle_log(self, checked):
        self.log_widget.setVisible(checked)
        if checked:
            self.btn_toggle_log.setText("Ẩn nhật ký ▲")
        else:
            self.btn_toggle_log.setText("Hiện nhật ký ▼")

    def on_copy_log(self):
        QApplication.clipboard().setText(self.txt_log.toPlainText())

    def on_start(self):
        if self.worker is not None and self.worker.isRunning():
            self.worker.cancel()
            self.start_btn.setEnabled(False)
            self.final_message = "<br><br><b>Đang hủy...</b>"
            self.update_progress_ui()
            self.log_message("Người dùng yêu cầu hủy...")
            return
            
        videos = self.video_list.get_videos()
        if not videos:
            return

        import os
        outdir_base = self.lbl_outdir.text()
        if outdir_base == "Chưa chọn thư mục" or not os.path.exists(outdir_base):
            self.log_message("LỖI: Vui lòng chọn thư mục xuất.")
            return

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        run_outdir = os.path.join(outdir_base, f"run_{timestamp}")
        try:
            os.makedirs(run_outdir, exist_ok=True)
        except Exception as e:
            self.log_message(f"LỖI: Không thể tạo thư mục {run_outdir}: {e}")
            return
            
        self.txt_log.clear()
        self.log_message(f"Bắt đầu xử lý {len(videos)} video...")
        self.log_message(f"Thư mục xuất: {run_outdir}")
        self.start_time = datetime.datetime.now()
        
        # Initialize statuses
        n_groups = len(group_videos_by_suffix(videos))
        self.group_statuses = ["pending"] * n_groups
        self.final_message = ""
        self.update_progress_ui()
        self.spinner_timer.start(100) # 100ms for smooth animation
        
        self.start_btn.setText("Hủy")
        self.add_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.worker = ProcessingWorker(
            videos=videos,
            output_dir=run_outdir,
            zoom_percent=self.spin_zoom_percent.value(),
            remove_sound=self.chk_mute.isChecked(),
            prefix=self.txt_prefix.text(),
            n_parallel=self.spin_parallel.value(),
            quality=self.cmb_quality.currentData(),
            logo_method=self.cmb_logo_method.currentData()
        )
        self.worker.run_outdir = run_outdir
        self.worker.group_started.connect(self.on_group_started)
        self.worker.group_failed.connect(self.on_group_failed)
        self.worker.group_done.connect(self.on_group_done)
        self.worker.all_done.connect(self.on_all_done)
        self.worker.start()
        
    def on_group_started(self, idx):
        if getattr(self, 'group_statuses', []) and idx < len(self.group_statuses):
            self.group_statuses[idx] = "processing"
            
    def on_group_done(self, idx):
        if getattr(self, 'group_statuses', []) and idx < len(self.group_statuses):
            self.group_statuses[idx] = "done"
            self.update_progress_ui()
            
    def on_group_failed(self, idx, err):
        self.log_message(f"LỖI Nhóm {idx + 1}:\n{err}")
        if getattr(self, 'group_statuses', []) and idx < len(self.group_statuses):
            self.group_statuses[idx] = "failed"
            self.update_progress_ui()

    def on_spinner_timer(self):
        self.spinner_idx = (self.spinner_idx + 1) % len(self.spinner_frames)
        self.update_progress_ui()

    def update_progress_ui(self):
        if not getattr(self, 'group_statuses', []):
            return
            
        html_parts = []
        for i, status in enumerate(self.group_statuses):
            if status == "pending":
                icon = "🕒"
                color = "gray"
            elif status == "processing":
                icon = self.spinner_frames[self.spinner_idx]
                color = "#0050b3"
            elif status == "done":
                icon = "✅"
                color = "green"
            elif status == "failed":
                icon = "❌"
                color = "red"
            else:
                icon = "?"
                color = "black"
                
            html_parts.append(f"<span style='color: {color};'>[{icon} Nhóm {i+1}]</span>")
            
        joined_spans = "&nbsp;&nbsp;".join(html_parts)
        
        final_text = joined_spans
        if getattr(self, 'final_message', ""):
            final_text += self.final_message
            
        self.lbl_progress.setText(final_text)

    def on_all_done(self, completed, failed):
        self.spinner_timer.stop()
        msg = f"Hoàn thành: {completed} thành công, {failed} lỗi"
        
        if self.start_time:
            end_time = datetime.datetime.now()
            duration = end_time - self.start_time
            total_seconds = int(duration.total_seconds())
            mins, secs = divmod(total_seconds, 60)
            time_str = f"{mins} phút {secs} giây" if mins > 0 else f"{secs} giây"
            log_msg = f"{msg}. Tổng thời gian: {time_str}"
        else:
            log_msg = msg
            
        run_outdir = getattr(self.worker, 'run_outdir', 'open_dir')
        href_path = run_outdir.replace('\\', '/') if run_outdir != 'open_dir' else run_outdir
        
        self.final_message = f'<br><br><b>{msg}</b> (<a href="{href_path}">Mở thư mục xuất</a>)'
        self.update_progress_ui()
        self.log_message(log_msg)
        self.start_btn.setText("Bắt đầu")
        self.start_btn.setEnabled(True)
        self.add_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
