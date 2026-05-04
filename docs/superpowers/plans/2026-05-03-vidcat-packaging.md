# VidCat Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package the VidCat application into a Windows `.exe` using PyInstaller, bundle the `ffmpeg` binary via `imageio-ffmpeg`, and provide an NSIS installer script.

**Architecture:** Use `imageio-ffmpeg` to automatically provide a local, cross-platform `ffmpeg` binary instead of relying on the system `PATH`. Configure PyInstaller with a `.spec` file to bundle the binary, PyQt6, and the app code into a single directory distribution (`--onedir`). Provide a `setup.nsi` for creating the final installer.

**Tech Stack:** PyInstaller, NSIS, `imageio-ffmpeg`

---

### Task 1: Integrate `imageio-ffmpeg`

**Files:**
- Modify: `requirements.txt`
- Modify: `core/ffmpeg_utils.py`
- Modify: `core/worker.py`
- Modify: `tests/core/test_worker.py`
- Modify: `tests/core/test_ffmpeg_utils.py`

- [ ] **Step 1: Add Dependency**
Modify `requirements.txt` to add `imageio-ffmpeg==0.6.0`.

- [ ] **Step 2: Update FFmpeg Utils**
In `core/ffmpeg_utils.py`, add `import imageio_ffmpeg`.
Update both `normalize_video` and `concat_videos` to pass `cmd=imageio_ffmpeg.get_ffmpeg_exe()` into the `ffmpeg.run(...)` calls:
```python
    ffmpeg.run(stream, cmd=imageio_ffmpeg.get_ffmpeg_exe(), quiet=True)
```
```python
    ffmpeg.run(stream, cmd=imageio_ffmpeg.get_ffmpeg_exe(), overwrite_output=True, quiet=True)
```

- [ ] **Step 3: Update Worker Resolution Parsing**
In `core/worker.py`, replace `ffmpeg.probe` with a subprocess call that parses `ffmpeg -i` output, since `imageio-ffmpeg` only bundles `ffmpeg` (not `ffprobe`).
```python
import subprocess
import re
import imageio_ffmpeg
```
Replace the `ffmpeg.probe` block with:
```python
                    # 1. Get target resolution from first video using ffmpeg
                    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                    try:
                        result = subprocess.run([ffmpeg_exe, "-i", group[0]], stderr=subprocess.PIPE, text=True)
                        output = result.stderr
                        # Find "Stream #...: Video: ... 1920x1080"
                        match = re.search(r'Video:.*?\s(\d{3,4})x(\d{3,4})', output)
                        if not match:
                            raise ValueError("Could not determine video resolution")
                        target_w = int(match.group(1))
                        target_h = int(match.group(2))
                    except Exception as e:
                        raise ValueError(f"Failed to read resolution: {e}")
```

- [ ] **Step 4: Fix Tests**
Update `tests/core/test_worker.py` to mock `subprocess.run`:
```python
    mock_run = mocker.MagicMock()
    mock_run.stderr = "Stream #0:0: Video: h264, yuv420p, 1280x720, 30 fps"
    mocker.patch('subprocess.run', return_value=mock_run)
```
Update `tests/core/test_ffmpeg_utils.py` to mock `imageio_ffmpeg.get_ffmpeg_exe`.

- [ ] **Step 5: Run tests and commit**
Run `pytest -v` to ensure it passes.
Commit: `git commit -m "feat: integrate imageio-ffmpeg for standalone packaging"`

---

### Task 2: PyInstaller Configuration

**Files:**
- Create: `assets/icon.ico`
- Create: `vidcat.spec`

- [ ] **Step 1: Create dummy icon**
Run: `mkdir -p assets && touch assets/icon.ico`

- [ ] **Step 2: Create `vidcat.spec`**
Create `vidcat.spec` with PyInstaller configuration:
```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/icon.ico', 'assets')],
    hiddenimports=['imageio_ffmpeg'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VidCat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VidCat',
)
```

- [ ] **Step 3: Commit**
Commit: `git commit -m "build: add PyInstaller spec and dummy icon"`

---

### Task 3: NSIS Installer Script

**Files:**
- Create: `installer/setup.nsi`

- [ ] **Step 1: Create Installer Script**
Run `mkdir -p installer`. Create `installer/setup.nsi`:
```nsis
!include "MUI2.nsh"

Name "VidCat"
OutFile "VidCat_Installer.exe"
InstallDir "$PROGRAMFILES64\VidCat"
RequestExecutionLevel admin

!define MUI_ABORTWARNING
!define MUI_ICON "..\assets\icon.ico"
!define MUI_UNICON "..\assets\icon.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "Vietnamese"

Section "VidCat (required)" SecCore
  SetOutPath "$INSTDIR"
  
  # Copy all files from the PyInstaller dist directory
  File /r "..\dist\VidCat\*.*"
  
  # Create Uninstaller
  WriteUninstaller "$INSTDIR\uninstall.exe"
  
  # Start Menu shortcut
  CreateDirectory "$SMPROGRAMS\VidCat"
  CreateShortcut "$SMPROGRAMS\VidCat\VidCat.lnk" "$INSTDIR\VidCat.exe" "" "$INSTDIR\assets\icon.ico"
  
  # Desktop shortcut
  CreateShortcut "$DESKTOP\VidCat.lnk" "$INSTDIR\VidCat.exe" "" "$INSTDIR\assets\icon.ico"
  
  # Registry keys for Add/Remove Programs
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\VidCat" "DisplayName" "VidCat"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\VidCat" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\VidCat" "DisplayIcon" "$INSTDIR\assets\icon.ico"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\VidCat" "Publisher" "VidCat Developer"
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\VidCat.lnk"
  Delete "$SMPROGRAMS\VidCat\VidCat.lnk"
  RMDir "$SMPROGRAMS\VidCat"
  
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\VidCat"
  
  RMDir /r "$INSTDIR"
SectionEnd
```

- [ ] **Step 2: Commit**
Commit: `git commit -m "build: add NSIS installer script"`
