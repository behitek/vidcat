# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

VidCat is a Windows/macOS/Linux desktop GUI app (Python 3.13 + PyQt6) for batch video processing: it groups input videos, removes logos/watermarks (zoom-crop or FFmpeg `delogo`), normalizes resolution, and concatenates each group into a single output file via FFmpeg. UI strings, logs, and user-facing docs are in Vietnamese.

## Commands

This project uses [uv](https://github.com/astral-sh/uv) for environment/dependency management.

```bash
# Install/sync dependencies (including dev group)
uv sync

# Run the app
uv run main.py

# Run all tests
uv run pytest

# Run a single test file / test
uv run pytest tests/core/test_worker.py
uv run pytest tests/core/test_worker.py::test_name -v

# Build a standalone executable (PyInstaller, config in vidcat.spec)
uv run pyinstaller -y vidcat.spec
# Output: dist/VidCat/VidCat.exe
```

Building the Windows installer (NSIS) requires `makensis.exe` and is a separate step after the PyInstaller build — see `DEPLOYMENT.md` for the full two-stage packaging process (`installer/setup.nsi` packages `dist/VidCat` into a single installer exe, kills any running `VidCat.exe` first via `taskkill`).

FFmpeg must be installed and on PATH when running from source (not needed for the packaged exe, which bundles `imageio-ffmpeg`'s FFmpeg binary).

## Architecture

Three-layer split, all wired together in `main.py`:

- **`ui/main_window.py`** — `MainWindow` (QMainWindow). Owns all widgets, persists user settings via `QSettings("VidcatDev", "Vidcat")` (mute, group size, parallelism, watermark method, prefix, output dir, tray toggle), builds a group-colored/labeled video list, drives a spinner-based per-group progress UI, manages a collapsible log panel, and supports minimize-to-System-Tray behavior. It creates and owns the `ProcessingWorker` instance for each run.
- **`ui/video_list.py`** — `VideoListWidget` (QListWidget subclass). Thin wrapper storing each video's full path in item data role `100`; `MainWindow` reads/writes this list directly (e.g. `update_video_groups` restyles item backgrounds/text based on current group size).
- **`core/worker.py`** — `ProcessingWorker` (QThread). Takes the video list, group size, parallelism, watermark method, mute flag, and output prefix. Splits videos into fixed-size groups and processes groups concurrently with a `ThreadPoolExecutor` (`n_parallel` workers). For each group: probes the first video's resolution via a direct FFmpeg subprocess call (regex over stderr), normalizes every video in the group to that resolution/watermark treatment into a temp dir, then concatenates the group into one output file. Emits Qt signals (`group_started`, `group_done`, `group_failed`, `all_done`) that `MainWindow` connects to for UI updates.
- **`core/ffmpeg_utils.py`** — Pure FFmpeg-command-building functions used by the worker: `normalize_video` (crop/scale/delogo filters, optional audio-stream detection via `ffprobe` when audio is kept) and `concat_videos` (writes an FFmpeg concat-demuxer list file, stream-copies). All FFmpeg processes run through `imageio_ffmpeg.get_ffmpeg_exe()` (bundled binary, no PATH dependency at runtime) and use `subprocess.run` directly (not `ffmpeg-python`'s `.run()`) so stdout/stderr can be captured quietly and Windows console windows suppressed (`creationflags=0x08000000`).

Key implementation details worth knowing before changing processing logic:
- Watermark removal is a *filter choice made during normalization*, not a separate pass: `zoom` crops 20% off each edge before scaling; `delogo` blurs two fixed-size regions (bottom-right and top-left) at 260x120px after scaling to the target resolution.
- Group target resolution is always taken from the *first video in the group*; all other videos in that group are scaled to match.
- Audio handling: when muted, video-only streams are output directly; when kept, `ffprobe` is used to check whether the source actually has an audio stream (avoids FFmpeg errors muxing a nonexistent audio track).
- Max parallelism offered in the UI is computed from both CPU count (`cpu_count - 1`) and available RAM (~1.5GB per concurrent FFmpeg task), taking the minimum (`MainWindow.get_max_parallel_tasks`).

## Testing

Tests use `pytest` + `pytest-qt` (for `MainWindow`/`VideoListWidget` widget tests) + `pytest-mock`, mirroring the `core`/`ui` package layout under `tests/`. `tests/conftest.py` provides a shared `temp_dir` fixture.
