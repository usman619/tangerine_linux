import os
import shutil
import zipfile
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import QFileDialog, QLabel, QVBoxLayout, QDialog
from PyQt6.QtGui import QGuiApplication, QPixmap
from PyQt6.QtCore import Qt


class FloatingPreviewWindow(QDialog):
    """Always-on-top picture-in-picture floating file card (Tangerine 'Float' feature)."""
    _open_windows: list["FloatingPreviewWindow"] = []

    def __init__(self, file_path: Path):
        super().__init__()
        self.setWindowTitle(f"Float: {file_path.name}")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setStyleSheet("background-color: #18181c; color: #ffffff; border-radius: 8px; padding: 8px;")

        layout = QVBoxLayout(self)
        label = QLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pixmap = QPixmap(str(file_path))
        if not pixmap.isNull():
            label.setPixmap(pixmap.scaled(320, 320, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            label.setText(f"📄 {file_path.name}\n({file_path.stat().st_size // 1024} KB)")

        layout.addWidget(label)
        self.resize(340, 340)
        self.show()
        FloatingPreviewWindow._open_windows.append(self)


class ActionWorker:
    @staticmethod
    def copy_path(file_paths: list[str]) -> str:
        clipboard = QGuiApplication.clipboard()
        paths_str = "\n".join(os.path.abspath(p) for p in file_paths)
        if clipboard is not None:
            clipboard.setText(paths_str)
        return f"Copied {len(file_paths)} path(s)"

    @staticmethod
    def open_terminal(file_path: str) -> str:
        folder = str(Path(file_path).parent)
        # Try common Linux terminal emulators first, fallback to file manager
        terminals = [
            ["gnome-terminal", f"--working-directory={folder}"],
            ["konsole", "--workdir", folder],
            ["xfce4-terminal", f"--working-directory={folder}"],
            ["kitty", "--directory", folder],
            ["alacritty", "--working-directory", folder],
            ["x-terminal-emulator", f"--working-directory={folder}"],
            ["xdg-open", folder],
        ]
        for cmd in terminals:
            if shutil.which(cmd[0]):
                subprocess.Popen(cmd)
                return f"Opened in {cmd[0]}"
        return "Could not find terminal"

    @staticmethod
    def float_files(file_paths: list[str]) -> str:
        for fp in file_paths[:3]:
            FloatingPreviewWindow(Path(fp))
        return f"Floating {min(len(file_paths), 3)} file(s)"

    @staticmethod
    def copy_or_move_files(file_paths: list[str], move: bool = False) -> str:
        dest_dir = QFileDialog.getExistingDirectory(None, "Select Destination Folder")
        if not dest_dir:
            return "Cancelled"
        dest_path = Path(dest_dir)
        for fp in file_paths:
            src = Path(fp)
            target = dest_path / src.name
            if move:
                shutil.move(str(src), str(target))
            else:
                shutil.copy2(str(src), str(target))
        verb = "Moved" if move else "Copied"
        return f"{verb} {len(file_paths)} file(s) to {dest_path.name}"

    @staticmethod
    def zip_for_share(file_paths: list[str], out_zip: Path) -> str:
        with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for fp in file_paths:
                p = Path(fp)
                zf.write(p, arcname=p.name)
        return out_zip.name