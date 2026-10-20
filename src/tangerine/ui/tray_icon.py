from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction
from PyQt6.QtCore import Qt
from tangerine.config import CONFIG

class TangerineTray(QSystemTrayIcon):
    def __init__(self, app: QApplication, on_summon_callback):
        super().__init__(self._build_icon(), app)
        self.setToolTip(f"{CONFIG.APP_NAME} (Drag + Shift)")

        menu = QMenu()
        summon_action = QAction("Summon Wheel (Shift)", app)
        summon_action.triggered.connect(on_summon_callback)

        quit_action = QAction("Quit", app)
        quit_action.triggered.connect(app.quit)

        menu.addAction(summon_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.setContextMenu(menu)

    @staticmethod
    def _build_icon() -> QIcon:
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        p = QPainter(pixmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor(255, 126, 20))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(8, 12, 48, 48)
        p.setBrush(QColor(60, 180, 75))
        p.drawEllipse(30, 2, 16, 10)
        p.end()
        return QIcon(pixmap)

    def notify_success(self, outputs: list[str]):
        summary = ", ".join(outputs[:3])
        if len(outputs) > 3:
            summary += f" (+{len(outputs) - 3} more)"
        self.showMessage(
            "Tangerine Converted ✓",
            f"Created: {summary}",
            QSystemTrayIcon.MessageIcon.Information,
            2500
        )