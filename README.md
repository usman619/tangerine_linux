# Open-Tangerine for Linux

**Drag. Tap. Already Done.**  
*A context-aware, Liquid Glass radial file converter and toolbox for Linux—right under your cursor.*

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![PyQt6](https://img.shields.io/badge/UI-PyQt6%20Liquid%20Glass-FF7E14?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Linux%20(X11%20%2F%20XWayland)-success?style=flat-square&logo=linux)
![License](https://img.shields.io/badge/License-GPL--3.0-orange?style=flat-square)

**Open-Tangerine for Linux** brings the iconic macOS *"Drag + Modifier"* radial workflow (inspired by [Tangerine for Mac](https://tangerineformac.com/) and [Open-Tangerine](https://github.com/sintaxerrorpvtltd/Open-Tangerine)) natively to the Linux desktop. 

Instead of opening bulky applications or uploading private files to sketchy cloud converters, simply **start dragging any file(s)** from your Linux file manager, tap **`Shift`**, **`Alt`**, or **`Ctrl`**, and drop the file onto a 60 FPS **Liquid Glass radial wheel** that blooms open directly beneath your cursor.

---

## Key Features

- **60 FPS Liquid Glass Radial UI:** Built with custom `QPainterPath` vector icons (zero emojis), refractive multi-stop gradients, specular rim lighting, and smooth spring hover physics.
- **Context-Aware Dynamic Slices:** The wheel automatically inspects the file extensions you are currently dragging and displays *only* the conversion targets and tools that make sense for those specific files.
- **100% Local & Non-Destructive:** Zero uploads, zero accounts, zero file size quotas. Original files are never modified, and existing output files are never overwritten (automatic `_1`, `_2` suffix protection).
- **Three Gesture Wheels in One:**
  - **`Shift` + Drag → Convert:** Instant single or batch format conversion across Images, Video, Audio, PDFs, Documents, Subtitles, and Data files.
  - **`Alt` + Drag → Toolbox:** Interactive mini-editors for Image/Media Compression, Resize & Rotate, Audio/Video Trimming, PDF Merging/Splitting, EXIF Metadata Stripping, and Archive/Audio Extraction.
  - **`Ctrl` + Drag → Quick Actions:** Picture-in-Picture Draggable Floating Shelf (`FLOAT`), Copy Absolute Path, Open Folder in Terminal, SHA-256 Checksum to Clipboard, Copy/Move to Folder, and Instant `.zip` Archiving.

---

## The 3 Gesture Modes

### 1. `Shift` while Dragging — **Convert Wheel** *(Tangerine Orange)*
Dynamically adapts its slices based on what you are holding:
| Input File Type | Available Radial Conversion Targets |
| :--- | :--- |
| **Images** (`.png`, `.jpg`, `.webp`, `.bmp`, `.tiff`, `.gif`, `.heic`, `.avif`) | `PNG`, `JPG`, `WEBP`, `PDF` *(combines multiple images into 1 PDF)*, `AVIF` |
| **Vectors** (`.svg`) | `PNG`, `PDF` *(high-resolution vector render via `QSvgRenderer`)* |
| **Videos** (`.mp4`, `.mkv`, `.mov`, `.webm`, `.avi`) | `MP4`, `WEBM`, `GIF`, `MP3`, `WAV` |
| **Audio** (`.mp3`, `.wav`, `.flac`, `.ogg`, `.m4a`, `.opus`) | `MP3`, `WAV`, `FLAC`, `OGG` |
| **PDF Documents** (`.pdf`) | `PNG`, `TXT` *(+ extracts embedded images)*, `DOCX`, or `PDF` *(merges multiple PDFs)* |
| **Subtitles** (`.srt`, `.vtt`) | `VTT`, `SRT`, `TXT` *(strips timestamps & cue numbers)* |
| **Structured Data** (`.csv`, `.json`) | `JSON` ↔ `CSV` |
| **Office / Docs** (`.docx`, `.md`, `.txt`, `.epub`) | `PDF`, `DOCX`, `EPUB`, `TXT` *(via Pandoc / LibreOffice)* |

### 2. `Alt` while Dragging — **Toolbox Wheel** *(Sky Cyan)*
| Tool Slice | Behavior |
| :--- | :--- |
| **COMPRESS** | Opens an interactive quality slider (`15%–95%`) for images or runs H.264 `CRF 28` / `128k` audio compression for media. |
| **RESIZE** | Opens an interactive scale (`10%–200%`) and rotation (`90°`, `180°`, `270°`) modal. |
| **CLEAN EXIF** | Strips all camera metadata and GPS coordinates while preserving upright EXIF photo orientation. |
| **MERGE** | Appears automatically when dragging 2+ PDFs or 2+ Images; binds them into a single PDF document. |
| **SPLIT** | Splits a multi-page PDF into individual `filename_page_N.pdf` files. |
| **TRIM** | Opens an interactive start-offset & duration trimmer for audio and video files (lossless stream copy via `ffmpeg`). |
| **EXTRACT** | Extracts text + embedded images from `.pdf`, rips `.mp3` audio from video files, or unpacks `.zip` archives. |

### 3. `Ctrl` while Dragging — **Actions Wheel** *(Amethyst Violet)*
| Action Slice | Behavior |
| :--- | :--- |
| **FLOAT** | Pins files into an always-on-top **Floating Shelf Window**. Drag files back *out* of the shelf into Discord, Slack, browsers, or other folders anytime. |
| **COPY PATH** | Copies the absolute file path(s) directly to your system clipboard. |
| **TERMINAL** | Opens your default Linux terminal emulator (`gnome-terminal`, `konsole`, `kitty`, `alacritty`, `xfce4-terminal`) directly in the file's parent directory. |
| **SHA256** | Computes the `SHA-256` cryptographic hash of the dropped file(s) and copies it to your clipboard. |
| **COPY / MOVE** | Prompts for a destination folder and copies or moves the batch cleanly. |
| **SHARE** | Bundles all dropped files into a compressed `_archive.zip` right next to the originals. |

---

## Project Architecture

```text
open-tangerine-linux/
├── pyproject.toml                  # Package metadata & CLI script entry point
├── README.md                       # Project documentation
└── src/
    └── tangerine/
        ├── __init__.py
        ├── main.py                 # Application bootstrap & QApplication event loop
        ├── config.py               # Wheel geometry, file extensions, & contextual slice rules
        ├── core/
        │   ├── __init__.py
        │   ├── dispatcher.py       # Non-destructive path resolver & worker router
        │   ├── image_worker.py     # Pillow image conversions, compression, resize, EXIF strip
        │   ├── pdf_worker.py       # pypdf merging, splitting, text & embedded image extraction
        │   ├── media_worker.py     # FFmpeg audio/video conversion, compression, & trimming
        │   ├── doc_worker.py       # SVG rendering, SRT/VTT subtitles, CSV/JSON, & SHA-256
        │   └── action_worker.py    # Drag-out Floating Shelf, clipboard, terminal, & zip actions
        ├── services/
        │   ├── __init__.py
        │   └── hotkey_listener.py  # Global pynput Drag + Modifier state machine
        └── ui/
            ├── __init__.py
            ├── theme.py            # Design tokens & reusable PyQt6 QSS stylesheet
            ├── icons.py            # Resolution-independent QPainterPath vector icon engine
            ├── dialogs.py          # Interactive Compress, Resize/Rotate, & Media Trim modals
            ├── radial_overlay.py   # 60 FPS Liquid Glass frameless radial drop widget
            └── tray_icon.py        # System tray integration & completion notifications
```
## Installation Guide
1. **System Prerequisites**
Install python3, venv, and ffmpeg (required for audio/video conversion and trimming). Optionally install pandoc or libreoffice for document conversions (.docx / .epub).

**Ubuntu / Debian / Linux Mint / Pop!_OS:**
```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip ffmpeg pandoc -y
```
**Fedora:**
```bash
sudo dnf install python3 python3-pip ffmpeg pandoc -y
```
**Arch Linux / Manjaro:**
```bash
sudo pacman -S python python-pip ffmpeg pandoc
```

2. **Clone & Set Up Virtual Environment**
```bash
git clone https://github.com/yourusername/open-tangerine-linux.git
cd open-tangerine-linux

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate
```
3. **Install Package & Dependencies**
Install the project in editable mode using pip:
```bash
pip install --upgrade pip
pip install -e .

# Optional: Install HEIC / AVIF image support
pip install pillow-heif
```
## Usage
### Running the Application
Once installed in your virtual environment, launch the background tray daemon with:
```bash
tangerine-linux
```
(Or run python3 -m tangerine.main directly).

### How to Convert or Process Files

Open your Linux file manager (Nautilus / Files, Dolphin, Nemo, Thunar, etc.).

Click and start dragging one or more files.

While holding the left mouse button down, tap your desired modifier key:

    - Tap Shift for Convert
    - Tap Alt for Toolbox
    - Tap Ctrl for Actions

Hover over your target slice on the radial wheel and release the mouse button.

Your converted file appears immediately right next to the original file!

**Linux Desktop Tip**: You only need to tap Shift, Alt, or Ctrl once after starting your drag to summon or switch wheels—you do not need to keep holding the key down when releasing the mouse button. This prevents your Linux file manager or window manager from intercepting Alt+Drop or Ctrl+Drop.

### Display Server Notes (X11 vs. Wayland)

- X11 Sessions (Ubuntu on Xorg, Linux Mint Cinnamon, XFCE, MATE, i3, AwesomeWM): Works out of the box with zero extra configuration.
- Wayland Sessions (GNOME Wayland, KDE Plasma Wayland, Hyprland, Sway):

1. Pure Wayland prevents windows from positioning themselves at arbitrary global cursor (x, y) coordinates. Force Qt to run through XWayland so the wheel spawns directly under your cursor:
    ```bash
    QT_QPA_PLATFORM=xcb tangerine-linux
    ```
2. If your Wayland compositor isolates keyboard events from pynput during drags, you can either summon the wheel from the System Tray icon or bind a global shortcut in your Desktop Environment settings.

## Acknowledgements

- Inspired by the original macOS concept Tangerine for Mac (https://tangerineformac.com/#).
- Inspired by the open-source initiative Open-Tangerine (https://github.com/sintaxerror-pvt/Open-Tangerine).
