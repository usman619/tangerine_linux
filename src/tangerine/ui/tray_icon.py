from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QColor, QAction
from tangerine.config import CONFIG
from tangerine.ui.icons import VectorIconEngine
from tangerine.ui.theme import get_app_stylesheet


class TangerineTray(QSystemTrayIcon):
    def __init__(self, app: QApplication, on_summon_callback):
        super().__init__(VectorIconEngine.as_qicon("TANGERINE", 64, QColor(255, 126, 20)), app)
        self.setToolTip(f"{CONFIG.APP_NAME} (Drag + Shift / Alt / Ctrl)")

        menu = QMenu()
        menu.setStyleSheet(get_app_stylesheet())

        summon_action = QAction("Summon Wheel (Shift)", app)
        summon_action.triggered.connect(on_summon_callback)

        quit_action = QAction("Quit", app)
        quit_action.triggered.connect(app.quit)

        menu.addAction(summon_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.setContextMenu(menu)

    def notify_success(self, outputs: list[str]) -> None:
        summary = ", ".join(outputs[:3])
        if len(outputs) > 3:
            summary += f" (+{len(outputs) - 3} more)"
        self.showMessage(
            "Tangerine Complete",
            summary,
            QSystemTrayIcon.MessageIcon.Information,
            2500
        )