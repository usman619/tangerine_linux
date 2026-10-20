import os
import shutil
import zipfile
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (
    QFileDialog, QLabel, QVBoxLayout, QHBoxLayout,
    QDialog, QPushButton, QFrame
)
from PyQt6.QtGui import QGuiApplication, QPixmap, QDrag
from PyQt6.QtCore import Qt, QMimeData, QUrl

from tangerine.ui.theme import get_app_stylesheet
from tangerine.core.doc_worker import DocWorker


class FloatingShelfWindow(QDialog):
    """Always-on-top Picture-in-Picture shelf that supports DRAGGING FILES OUT into other apps."""
    _open_windows: list["FloatingShelfWindow"] = []

    def __init__(self, file_paths: list[str]):
        super().__init__()
        self.file_paths = [Path(p) for p in file_paths if os.path.exists(p)]
        self.setWindowTitle("Tangerine Float Shelf")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet(get_app_stylesheet())

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        # Header Bar
        header = QHBoxLayout()
        title = QLabel(f"Floating Shelf ({len(self.file_paths)} file{'s' if len(self.file_paths) > 1 else ''})")
        title.setObjectName("HeadingLabel")
        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(64)
        close_btn.clicked.connect(self.close)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(close_btn)
        layout.addLayout(header)

        # Preview Area
        preview = QLabel()
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        first = self.file_paths[0]
        pixmap = QPixmap(str(first))
        if not pixmap.isNull():
            preview.setPixmap(pixmap.scaled(260, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            names = "\n".join(p.name for p in self.file_paths[:4])
            preview.setText(f"{names}\n\n({first.stat().st_size // 1024} KB)")
        layout.addWidget(preview)

        hint = QLabel("Drag anywhere from this card to drop files into another app")
        hint.setObjectName("MutedLabel")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        outer.addWidget(card)
        self.resize(310, 290)
        self.show()
        FloatingShelfWindow._open_windows.append(self)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setUrls([QUrl.fromLocalFile(str(p)) for p in self.file_paths])
            drag.setMimeData(mime)
            drag.exec(Qt.DropAction.CopyAction)


class ActionWorker:
    @staticmethod
    def copy_path(file_paths: list[str]) -> str:
        clipboard = QGuiApplication.clipboard()
        paths_str = "\n".join(os.path.abspath(p) for p in file_paths)
        if clipboard is not None:
            clipboard.setText(paths_str)
        return f"Copied {len(file_paths)} path(s)"

    @staticmethod
    def copy_sha256(file_paths: list[str]) -> str:
        hashes = []
        for fp in file_paths:
            p = Path(fp)
            digest = DocWorker.compute_sha256(p)
            hashes.append(f"{digest}  {p.name}")
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText("\n".join(hashes))
        return f"SHA-256 copied ({hashes[0][:12]}...)"

    @staticmethod
    def open_terminal(file_path: str) -> str:
        folder = str(Path(file_path).parent)
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
        FloatingShelfWindow(file_paths)
        return f"Floating {len(file_paths)} file(s)"

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