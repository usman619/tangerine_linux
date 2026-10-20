from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QSpinBox, QComboBox, QPushButton, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from tangerine.ui.theme import get_app_stylesheet


class BaseToolDialog(QDialog):
    def __init__(self, title_text: str):
        super().__init__()
        self.setWindowTitle(title_text)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet(get_app_stylesheet())
        self.resize(340, 200)
        pos = QCursor.pos()
        self.move(pos.x() - 170, pos.y() - 100)


class CompressDialog(BaseToolDialog):
    def __init__(self):
        super().__init__("Tangerine Compress")
        layout = QVBoxLayout(self)
        card = QFrame()
        card.setObjectName("Card")
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(12)

        heading = QLabel("Compression Quality")
        heading.setObjectName("HeadingLabel")
        c_layout.addWidget(heading)

        self.val_label = QLabel("Quality: 65% (Balanced)")
        self.val_label.setObjectName("MutedLabel")
        c_layout.addWidget(self.val_label)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(15, 95)
        self.slider.setValue(65)
        self.slider.valueChanged.connect(lambda v: self.val_label.setText(f"Quality: {v}%"))
        c_layout.addWidget(self.slider)

        btns = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        apply_btn = QPushButton("Compress Now")
        apply_btn.setObjectName("PrimaryButton")
        apply_btn.clicked.connect(self.accept)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(apply_btn)
        c_layout.addLayout(btns)
        layout.addWidget(card)

    @property
    def quality(self) -> int:
        return self.slider.value()


class ResizeRotateDialog(BaseToolDialog):
    def __init__(self):
        super().__init__("Tangerine Resize & Rotate")
        layout = QVBoxLayout(self)
        card = QFrame()
        card.setObjectName("Card")
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(12)

        heading = QLabel("Resize & Rotate Image")
        heading.setObjectName("HeadingLabel")
        c_layout.addWidget(heading)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Scale (%):"))
        self.scale_spin = QSpinBox()
        self.scale_spin.setRange(10, 200)
        self.scale_spin.setSingleStep(10)
        self.scale_spin.setValue(50)
        row1.addWidget(self.scale_spin)
        c_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Rotate:"))
        self.rot_combo = QComboBox()
        self.rot_combo.addItems(["0° (None)", "90° Clockwise", "180° Flip", "270° Counter-CW"])
        row2.addWidget(self.rot_combo)
        c_layout.addLayout(row2)

        btns = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        apply_btn = QPushButton("Apply Transform")
        apply_btn.setObjectName("PrimaryButton")
        apply_btn.clicked.connect(self.accept)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(apply_btn)
        c_layout.addLayout(btns)
        layout.addWidget(card)

    @property
    def params(self) -> tuple[int, int]:
        rot_map = {0: 0, 1: 90, 2: 180, 3: 270}
        return self.scale_spin.value(), rot_map.get(self.rot_combo.currentIndex(), 0)


class TrimMediaDialog(BaseToolDialog):
    def __init__(self):
        super().__init__("Tangerine Media Trim")
        layout = QVBoxLayout(self)
        card = QFrame()
        card.setObjectName("Card")
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(12)

        heading = QLabel("Trim Audio / Video Clip")
        heading.setObjectName("HeadingLabel")
        c_layout.addWidget(heading)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Start Offset (sec):"))
        self.start_spin = QSpinBox()
        self.start_spin.setRange(0, 7200)
        self.start_spin.setValue(0)
        row1.addWidget(self.start_spin)
        c_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Clip Duration (sec):"))
        self.dur_spin = QSpinBox()
        self.dur_spin.setRange(1, 7200)
        self.dur_spin.setValue(15)
        row2.addWidget(self.dur_spin)
        c_layout.addLayout(row2)

        btns = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        apply_btn = QPushButton("Save Trimmed Clip")
        apply_btn.setObjectName("PrimaryButton")
        apply_btn.clicked.connect(self.accept)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(apply_btn)
        c_layout.addLayout(btns)
        layout.addWidget(card)

    @staticmethod
    def _fmt_sec(sec: int) -> str:
        h, rem = divmod(sec, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    @property
    def timestamps(self) -> tuple[str, str]:
        return self._fmt_sec(self.start_spin.value()), self._fmt_sec(self.dur_spin.value())