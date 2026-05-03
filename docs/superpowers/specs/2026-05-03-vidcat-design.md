# VidCat — Design Specification
**Date:** 2026-05-03  
**Status:** Approved  
**Language:** Vietnamese UI, Windows target

---

## Overview

VidCat is a Windows desktop application that allows users to concatenate groups of short videos (each ~8 seconds) into single output videos. Users load a set of input videos, configure grouping options, and the app processes each group sequentially — producing one output file per group.

**Target user:** Vietnamese-speaking Windows users working with Veo-generated short video clips.

---

## Tech Stack

| Component | Choice | Rationale |
|---|---|---|
| GUI framework | PyQt6 | Native Windows look, strong widget set, Vietnamese-friendly |
| Video processing | OpenCV (`opencv-python`) | CPU-based inpainting per frame |
| Concat / audio | FFmpeg via `ffmpeg-python` | Fast, reliable, no re-encode for same-codec |
| Packaging | PyInstaller (`--onedir`) | Avoids AV false positives from self-extracting exe |
| Installer | NSIS | Standard Windows installer with uninstaller |

---

## Architecture

The app runs as a single Python process with two layers:

### GUI Layer (Main Thread)
- PyQt6 `QMainWindow` with three stacked panels (Input, Settings, Progress)
- Emits start/cancel signals to the Processing Layer
- Receives progress signals from the QThread worker and updates UI

### Processing Layer (QThread)
- One `ProcessingWorker(QThread)` instance, runs sequentially through each group
- Emits signals: `group_started(int)`, `frame_progress(int, int)`, `group_done(int)`, `group_failed(int, str)`, `all_done()`
- All temp files are created and cleaned up per group

---

## UI Components

### ① Input Panel
- **"Thêm video"** button — opens multi-file picker (`.mp4`, `.mov`, `.avi`, `.mkv`)
- Drag-and-drop list displaying videos in order:
  - Columns: `#`, thumbnail (first frame), filename, duration
  - Rows are drag-reorderable
  - Per-row **"Xóa"** (Remove) button
- Group boundaries are visually indicated by alternating row background colors, computed dynamically from the current "videos per group" setting

### ② Settings Panel
| Label (Vietnamese) | Control | Default |
|---|---|---|
| Tắt âm thanh | Toggle checkbox | ✅ ON |
| Số video mỗi nhóm | Spinbox (2–10) | 2 |
| Xóa watermark | Toggle checkbox | ✅ ON |
| Tiền tố tên file | Text input | `output` |
| Thư mục xuất | Path display + Browse button | *(required before start)* |

### ③ Progress Panel
- Overall label: `Đang xử lý nhóm 3 / 8`
- Per-group status list:
  - ✅ Completed groups
  - ⏳ Current group (with frame-level sub-progress bar)
  - ⬜ Pending groups
  - ❌ Failed groups (with truncated error message on hover)
- **"Bắt đầu"** button — disabled until output folder is set; becomes **"Hủy"** during processing

---

## Video Processing Pipeline

For each concat group, the `ProcessingWorker` executes these steps in order:

### Step 1 — Resolution Normalization (FFmpeg)
Scale all videos in the group to match the first video's resolution.  
Output: `tmp_{group_idx}_v{n}.mp4` in system temp directory.

### Step 2 — Watermark Removal (OpenCV, if enabled)
- Decode each temp video frame-by-frame using `cv2.VideoCapture`
- Apply a fixed mask over the bottom-right **200 × 50 px** region
- Run `cv2.inpaint(frame, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)` per frame
- Write inpainted frames back to a new temp file using `cv2.VideoWriter`
- Emit `frame_progress(current_frame, total_frames)` per frame for UI sub-progress

### Step 3 — Concat + Audio Strip (FFmpeg)
- Write a temporary FFmpeg concat list file
- Run FFmpeg using the concat demuxer (fast path — no re-encode when codecs match)
- If "Remove sound" is ON: pass `-an` flag
- Output file: `{output_dir}/{prefix}_{group_idx:03d}.mp4`

### Step 4 — Cleanup
Delete all temp files generated for this group before processing the next group.

### Error Handling
- If any step fails for a group: emit `group_failed(group_idx, error_message)`, mark group ❌, continue to next group
- At the end, report total completed vs. failed count

---

## Watermark Removal Detail

- **Algorithm:** Telea inpainting (`cv2.INPAINT_TELEA`)
- **Mask region:** Fixed rectangle, bottom-right corner, **200px wide × 50px tall**
  - Coordinates: `(width-200, height-50)` to `(width, height)`
- **Inpaint radius:** 3 pixels
- **CPU-only:** No GPU dependency
- **Constraint:** Assumes "veo" watermark is always in the bottom-right corner at consistent size. If watermark position varies, the fixed region may need adjustment via a future config option.

---

## Output

- **Format:** MP4
- **Codec:** Inherited from input (no re-encode in concat step)
- **Naming:** `{prefix}_{group_idx:03d}.mp4` — e.g., `output_001.mp4`, `output_002.mp4`
- **Location:** User-selected output folder

---

## Project Structure

```
vidcat/
├── main.py                  # App entry point
├── ui/
│   ├── main_window.py       # QMainWindow — assembles all panels
│   └── video_list.py        # Drag-and-drop QListWidget subclass
├── core/
│   ├── worker.py            # ProcessingWorker(QThread)
│   ├── inpainting.py        # OpenCV watermark removal logic
│   └── ffmpeg_utils.py      # FFmpeg subprocess wrappers (normalize, concat)
├── assets/
│   └── icon.ico             # App icon
├── installer/
│   └── setup.nsi            # NSIS installer script
├── docs/
│   └── superpowers/specs/
│       └── 2026-05-03-vidcat-design.md
└── requirements.txt
```

---

## Packaging & Distribution

### PyInstaller
- Mode: `--onedir` (folder, not single file) to avoid AV false positives
- Includes: Python runtime, PyQt6, OpenCV, ffmpeg binary (via `imageio-ffmpeg`)
- Entry point: `main.py`
- Icon: `assets/icon.ico`

### NSIS Installer
- Default install path: `C:\Program Files\VidCat`
- Creates Start Menu shortcut
- Creates Desktop shortcut (user opt-in during install)
- Registers uninstaller in Windows Add/Remove Programs
- Optional: install to `%APPDATA%` for no-admin-rights mode

---

## Constraints & Assumptions

- Input videos are short (~8 seconds each); CPU inpainting is feasible within reasonable time
- All input videos in a group are expected to be the same codec (H.264); resolution mismatches are handled by auto-scaling to the first video
- The "veo" watermark is always positioned in the bottom-right corner at a consistent size
- The app targets Windows 10/11 x64
- No internet connection required at runtime
