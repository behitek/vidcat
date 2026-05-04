# VidCat Wiring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the VidCat UI events to trigger the background ProcessingWorker and implement the actual video processing logic (scaling, watermark removal, concatenating).

**Architecture:** Connect PyQt6 signals/slots from the main window to UI update methods, implement the QThread `run()` method with sequential group processing and temp file cleanup, and handle real-time progress events.

**Tech Stack:** Python, PyQt6, OpenCV, tempfile

---

### Task 1: UI - File Browse Logic

**Files:**
- Modify: `ui/main_window.py`
- Modify: `tests/ui/test_main_window.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/ui/test_main_window.py`:
```python
from unittest.mock import patch

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `source venv/bin/activate && PYTHONPATH=. pytest tests/ui/test_main_window.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

Modify `ui/main_window.py`. Add imports:
```python
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QCheckBox, QSpinBox, QLineEdit, QLabel, QFileDialog
```
Add methods to `MainWindow` and connect signals in `__init__`:
```python
        # in __init__ at the end
        self.btn_outdir.clicked.connect(self.on_browse_outdir)
        self.add_btn.clicked.connect(self.on_add_video)
        
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `source venv/bin/activate && PYTHONPATH=. pytest tests/ui/test_main_window.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ui/main_window.py tests/ui/test_main_window.py
git commit -m "feat: add browse folder and file selection logic"
```

---

### Task 2: Worker - Group Iteration

**Files:**
- Modify: `core/worker.py`
- Modify: `tests/core/test_worker.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/core/test_worker.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `source venv/bin/activate && PYTHONPATH=. pytest tests/core/test_worker.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

Update `core/worker.py` `run` method:
```python
    def run(self):
        groups = [self.videos[i:i + self.group_size] for i in range(0, len(self.videos), self.group_size)]
        completed = 0
        failed = 0
        
        for idx, group in enumerate(groups):
            if self.is_cancelled:
                break
                
            self.group_started.emit(idx)
            
            try:
                # Stub for actual processing
                pass
                
                completed += 1
                self.group_done.emit(idx)
            except Exception as e:
                failed += 1
                self.group_failed.emit(idx, str(e))
                
        self.all_done.emit(completed, failed)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `source venv/bin/activate && PYTHONPATH=. pytest tests/core/test_worker.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/worker.py tests/core/test_worker.py
git commit -m "feat: implement worker group iteration"
```

---

### Task 3: Worker - Processing Pipeline

**Files:**
- Modify: `core/worker.py`
- Modify: `tests/core/test_worker.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/core/test_worker.py`:
```python
def test_worker_pipeline(qtbot, mocker):
    videos = ["1.mp4", "2.mp4"]
    worker = ProcessingWorker(videos, "out_dir", 2, True, True, "out")
    
    mock_norm = mocker.patch('core.worker.normalize_video')
    mock_remove = mocker.patch('core.worker.remove_watermark')
    mock_concat = mocker.patch('core.worker.concat_videos')
    mock_cap = mocker.MagicMock()
    mock_cap.get.side_effect = [1280, 720]
    mocker.patch('cv2.VideoCapture', return_value=mock_cap)
    
    worker.run()
    
    assert mock_norm.call_count == 2
    assert mock_remove.call_count == 2
    assert mock_concat.call_count == 1
    mock_concat.assert_called_once()
    assert "out_000.mp4" in mock_concat.call_args[0][1]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `source venv/bin/activate && PYTHONPATH=. pytest tests/core/test_worker.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

Modify `core/worker.py`. Add `import cv2`. Update `run` method:
```python
import cv2

# ... inside ProcessingWorker.run() loop ...
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    # 1. Get target resolution from first video
                    cap = cv2.VideoCapture(group[0])
                    target_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    target_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    cap.release()
                    
                    processed_paths = []
                    
                    for v_idx, video_path in enumerate(group):
                        if self.is_cancelled:
                            break
                            
                        # Normalize
                        norm_path = os.path.join(temp_dir, f"norm_{v_idx}.mp4")
                        normalize_video(video_path, norm_path, target_w, target_h)
                        current_path = norm_path
                        
                        # Watermark
                        if self.remove_watermark_flag:
                            wm_path = os.path.join(temp_dir, f"wm_{v_idx}.mp4")
                            remove_watermark(current_path, wm_path, lambda f, t: self.frame_progress.emit(f, t))
                            current_path = wm_path
                            
                        processed_paths.append(current_path)
                        
                    if self.is_cancelled:
                        break
                        
                    # Concat
                    out_path = os.path.join(self.output_dir, f"{self.prefix}_{idx:03d}.mp4")
                    concat_videos(processed_paths, out_path, temp_dir, self.remove_sound)
                
                completed += 1
                self.group_done.emit(idx)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `source venv/bin/activate && PYTHONPATH=. pytest tests/core/test_worker.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/worker.py tests/core/test_worker.py
git commit -m "feat: complete worker video processing pipeline"
```

---

### Task 4: UI - Start Worker and Progress

**Files:**
- Modify: `ui/main_window.py`
- Modify: `tests/ui/test_main_window.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/ui/test_main_window.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `source venv/bin/activate && PYTHONPATH=. pytest tests/ui/test_main_window.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

Modify `ui/main_window.py`. Add `from core.worker import ProcessingWorker`.
Add methods to `MainWindow`:
```python
        # in __init__
        self.start_btn.clicked.connect(self.on_start)
        self.worker = None

    def on_start(self):
        if self.worker is not None and self.worker.isRunning():
            self.worker.cancel()
            self.start_btn.setEnabled(False)
            self.lbl_progress.setText("Đang hủy...")
            return
            
        videos = self.video_list.get_videos()
        if not videos:
            return
            
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
        self.worker.all_done.connect(self.on_all_done)
        self.worker.start()
        
    def on_all_done(self, completed, failed):
        self.lbl_progress.setText(f"Hoàn thành: {completed} thành công, {failed} lỗi")
        self.start_btn.setText("Bắt đầu")
        self.start_btn.setEnabled(True)
        self.add_btn.setEnabled(True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `source venv/bin/activate && PYTHONPATH=. pytest tests/ui/test_main_window.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ui/main_window.py tests/ui/test_main_window.py
git commit -m "feat: wire start button to processing worker"
```
