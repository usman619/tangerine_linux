import math
import threading
from typing import Any
from PyQt6.QtWidgets import QWidget, QDialog
from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QFont, QCursor,
    QPainterPath, QLinearGradient, QRadialGradient, QBrush
)

from tangerine.config import CONFIG
from tangerine.core.dispatcher import ConversionDispatcher
from tangerine.core.action_worker import ActionWorker
from tangerine.ui.icons import VectorIconEngine
from tangerine.ui.dialogs import CompressDialog, ResizeRotateDialog, TrimMediaDialog


class RadialDropOverlay(QWidget):
    action_completed = pyqtSignal(list)

    MODE_META = {
        "CONVERT": ("CONVERT", "SHIFT", QColor(255, 126, 20)),   # Tangerine Orange
        "TOOLS":   ("TOOLBOX", "ALT",   QColor(14, 165, 233)),   # Sky Cyan
        "ACTIONS": ("ACTIONS", "CTRL",  QColor(139, 92, 246)),   # Violet
    }

    def __init__(self):
        super().__init__()
        self.current_mode = "CONVERT"
        self.hovered_index = -1
        self._dragged_files: list[str] = []
        self._active_targets: tuple[str, ...] = CONFIG.WHEELS["CONVERT"]

        self._open_progress = 0.0
        self._hover_weights: list[float] = [0.0] * len(self._active_targets)

        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)
        self._anim_timer.timeout.connect(self._tick_animation)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAcceptDrops(True)
        self.resize(CONFIG.WINDOW_SIZE, CONFIG.WINDOW_SIZE)

    def _refresh_targets(self) -> None:
        self._active_targets = CONFIG.get_contextual_slices(self.current_mode, self._dragged_files)
        if len(self._hover_weights) != len(self._active_targets):
            self._hover_weights = [0.0] * len(self._active_targets)
            self.hovered_index = -1

    def summon(self, mode: str = "CONVERT") -> None:
        was_visible = self.isVisible()
        self.current_mode = mode
        self._refresh_targets()

        if not was_visible:
            pos = QCursor.pos()
            half = CONFIG.WINDOW_SIZE // 2
            self.move(pos.x() - half, pos.y() - half)
            self.hovered_index = -1
            self._open_progress = 0.25
            self.show()
            self.raise_()

        if not self._anim_timer.isActive():
            self._anim_timer.start()
        self.update()

    def hideEvent(self, event) -> None:
        self._anim_timer.stop()
        self._dragged_files = []
        super().hideEvent(event)

    def _tick_animation(self) -> None:
        needs_repaint = False
        if self._open_progress < 1.0:
            self._open_progress = min(1.0, self._open_progress + (1.0 - self._open_progress) * 0.28 + 0.02)
            needs_repaint = True

        targets = self._active_targets
        if len(self._hover_weights) != len(targets):
            self._hover_weights = [0.0] * len(targets)

        for i in range(len(targets)):
            goal = 1.0 if i == self.hovered_index else 0.0
            current = self._hover_weights[i]
            if abs(goal - current) > 0.008:
                self._hover_weights[i] = current + (goal - current) * 0.26
                needs_repaint = True
            else:
                self._hover_weights[i] = goal

        if not needs_repaint and self._open_progress >= 1.0:
            self._anim_timer.stop()
        self.update()

    def _get_sector_at(self, pos: QPoint) -> int:
        targets = self._active_targets
        if not targets:
            return -1
        center = CONFIG.WINDOW_SIZE / 2
        dx, dy = pos.x() - center, pos.y() - center
        dist = math.hypot(dx, dy)

        if dist < CONFIG.INNER_RADIUS - 6 or dist > CONFIG.OUTER_RADIUS + 22:
            return -1

        angle = math.degrees(math.atan2(dy, dx)) % 360
        span = 360 / len(targets)
        return int(angle // span)

    # --- Context-Aware Drag & Drop Handlers ---
    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            self._dragged_files = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
            self._refresh_targets()
            self.update()
            event.accept()

    def dragMoveEvent(self, event) -> None:
        idx = self._get_sector_at(event.position().toPoint())
        if idx != self.hovered_index:
            self.hovered_index = idx
            if not self._anim_timer.isActive():
                self._anim_timer.start()
        event.accept()

    def dragLeaveEvent(self, event) -> None:
        self.hovered_index = -1
        if not self._anim_timer.isActive():
            self._anim_timer.start()

    def dropEvent(self, event) -> None:
        idx = self._get_sector_at(event.position().toPoint())
        targets = self._active_targets
        mode = self.current_mode
        file_paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        self.hide()

        if idx == -1 or idx >= len(targets) or not file_paths:
            return

        target_action = targets[idx]
        event.accept()

        # 1. GUI-bound Actions on Main Thread
        if mode == "ACTIONS" and target_action in ("FLOAT", "COPY", "MOVE"):
            if target_action == "FLOAT":
                msg = ActionWorker.float_files(file_paths)
            elif target_action == "COPY":
                msg = ActionWorker.copy_or_move_files(file_paths, move=False)
            else:
                msg = ActionWorker.copy_or_move_files(file_paths, move=True)
            self.action_completed.emit([msg])
            return

        # 2. Interactive Mini-Editors for Tools (Main Thread Dialog -> Background Worker)
        options: dict[str, Any] = {}
        if mode == "TOOLS":
            if target_action == "COMPRESS":
                dlg = CompressDialog()
                if dlg.exec() != QDialog.DialogCode.Accepted:
                    return
                options["quality"] = dlg.quality
            elif target_action == "RESIZE":
                dlg = ResizeRotateDialog()
                if dlg.exec() != QDialog.DialogCode.Accepted:
                    return
                scale, rot = dlg.params
                options["scale"] = scale
                options["rotate"] = rot
            elif target_action == "TRIM":
                dlg = TrimMediaDialog()
                if dlg.exec() != QDialog.DialogCode.Accepted:
                    return
                start_t, dur_t = dlg.timestamps
                options["start"] = start_t
                options["duration"] = dur_t

        threading.Thread(
            target=self._run_dispatch,
            args=(file_paths, mode, target_action, options),
            daemon=True
        ).start()

    def _run_dispatch(self, file_paths: list[str], mode: str, target: str, options: dict[str, Any]) -> None:
        outputs = ConversionDispatcher.dispatch(file_paths, mode, target, options)
        if outputs:
            self.action_completed.emit(outputs)

    # ==========================================================
    # LIQUID GLASS + VECTOR ICON RENDERER
    # ==========================================================
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        center = CONFIG.WINDOW_SIZE / 2
        center_pt = QPointF(center, center)
        targets = self._active_targets
        if not targets:
            return

        num_slices = len(targets)
        span = 360.0 / num_slices
        gap = CONFIG.SLICE_GAP_DEG

        mode_title, mod_key, accent_color = self.MODE_META.get(
            self.current_mode, ("CONVERT", "SHIFT", QColor(255, 126, 20))
        )

        scale = 0.84 + 0.16 * self._open_progress
        painter.save()
        painter.translate(center, center)
        painter.scale(scale, scale)
        painter.translate(-center, -center)

        # LAYER 1: Ambient Glow & Frosted Base Track
        ambient_glow = QRadialGradient(center_pt, CONFIG.OUTER_RADIUS + 34)
        ambient_glow.setColorAt(0.0, QColor(0, 0, 0, 0))
        ambient_glow.setColorAt(0.35, QColor(11, 13, 19, 130))
        ambient_glow.setColorAt(0.78, QColor(11, 13, 19, 165))
        ambient_glow.setColorAt(0.92, QColor(accent_color.red(), accent_color.green(), accent_color.blue(), 38))
        ambient_glow.setColorAt(1.0, QColor(0, 0, 0, 0))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(ambient_glow))
        painter.drawEllipse(center_pt, CONFIG.OUTER_RADIUS + 34, CONFIG.OUTER_RADIUS + 34)

        casing_outer = CONFIG.OUTER_RADIUS + 7
        casing_inner = CONFIG.INNER_RADIUS - 5
        casing_path = QPainterPath()
        casing_path.addEllipse(center_pt, casing_outer, casing_outer)
        inner_cutout = QPainterPath()
        inner_cutout.addEllipse(center_pt, casing_inner, casing_inner)
        casing_path = casing_path.subtracted(inner_cutout)

        casing_grad = QLinearGradient(
            center - casing_outer, center - casing_outer,
            center + casing_outer, center + casing_outer
        )
        casing_grad.setColorAt(0.0, QColor(255, 255, 255, 42))
        casing_grad.setColorAt(0.45, QColor(18, 21, 30, 165))
        casing_grad.setColorAt(1.0, QColor(11, 13, 19, 205))

        rim_grad = QLinearGradient(
            center - casing_outer, center - casing_outer,
            center + casing_outer, center + casing_outer
        )
        rim_grad.setColorAt(0.0, QColor(255, 255, 255, 115))
        rim_grad.setColorAt(0.5, QColor(255, 255, 255, 28))
        rim_grad.setColorAt(1.0, QColor(255, 255, 255, 60))

        painter.setBrush(QBrush(casing_grad))
        painter.setPen(QPen(QBrush(rim_grad), 1.2))
        painter.drawPath(casing_path)

        # LAYER 2: Contextual Liquid Glass Slices
        for i, label in enumerate(targets):
            weight = self._hover_weights[i] if i < len(self._hover_weights) else 0.0
            r_out = CONFIG.OUTER_RADIUS + (14.0 * weight)
            r_in = CONFIG.INNER_RADIUS + (2.5 * weight)

            start_deg = i * span + (gap / 2.0)
            slice_span = span - gap
            qt_start = -start_deg

            outer_rect = QRectF(center - r_out, center - r_out, r_out * 2, r_out * 2)
            inner_rect = QRectF(center - r_in, center - r_in, r_in * 2, r_in * 2)

            path = QPainterPath()
            path.arcMoveTo(outer_rect, qt_start)
            path.arcTo(outer_rect, qt_start, -slice_span)
            path.arcTo(inner_rect, qt_start - slice_span, slice_span)
            path.closeSubpath()

            mid_rad = math.radians(start_deg + slice_span / 2.0)
            mid_r = (r_in + r_out) / 2.0
            sx = center + mid_r * math.cos(mid_rad)
            sy = center + mid_r * math.sin(mid_rad)

            glass_grad = QLinearGradient(sx - 45, sy - 45, sx + 45, sy + 45)
            if weight > 0.01:
                ar, ag, ab = accent_color.red(), accent_color.green(), accent_color.blue()
                top_r = int(45 + (min(255, ar + 40) - 45) * weight)
                top_g = int(50 + (min(255, ag + 40) - 50) * weight)
                top_b = int(66 + (min(255, ab + 40) - 66) * weight)

                bot_r = int(20 + (ar - 20) * weight)
                bot_g = int(23 + (ag - 23) * weight)
                bot_b = int(34 + (ab - 34) * weight)

                glass_grad.setColorAt(0.0, QColor(255, 255, 255, int(90 + 115 * weight)))
                glass_grad.setColorAt(0.22, QColor(top_r, top_g, top_b, int(175 + 65 * weight)))
                glass_grad.setColorAt(1.0, QColor(bot_r, bot_g, bot_b, int(185 + 60 * weight)))
            else:
                glass_grad.setColorAt(0.0, QColor(255, 255, 255, 58))
                glass_grad.setColorAt(0.25, QColor(30, 35, 48, 165))
                glass_grad.setColorAt(1.0, QColor(16, 19, 27, 185))

            border_grad = QLinearGradient(sx - 50, sy - 50, sx + 50, sy + 50)
            border_grad.setColorAt(0.0, QColor(255, 255, 255, int(130 + 120 * weight)))
            border_grad.setColorAt(0.5, QColor(
                accent_color.red(), accent_color.green(), accent_color.blue(), int(40 + 170 * weight)
            ))
            border_grad.setColorAt(1.0, QColor(255, 255, 255, int(28 + 75 * weight)))

            painter.setBrush(QBrush(glass_grad))
            painter.setPen(QPen(QBrush(border_grad), 1.2 + 1.1 * weight))
            painter.drawPath(path)

            # LAYER 3: Custom Vector Icon + Typography
            icon_color = QColor(255, 255, 255, int(200 + 55 * weight))
            VectorIconEngine.draw(painter, label, QPointF(sx, sy - 10), size=18.0 + 2.0 * weight, color=icon_color)

            label_font = QFont("Inter", 8, QFont.Weight.Bold)
            label_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.7)
            painter.setFont(label_font)

            painter.setPen(QColor(0, 0, 0, 160))
            painter.drawText(QRectF(sx - 43, sy + 3, 88, 20), Qt.AlignmentFlag.AlignCenter, label)

            painter.setPen(QColor(243, 244, 246, int(215 + 40 * weight)))
            painter.drawText(QRectF(sx - 44, sy + 2, 88, 20), Qt.AlignmentFlag.AlignCenter, label)

        # LAYER 4: Central Glass Core Hub
        hub_r = CONFIG.INNER_RADIUS - 8
        hub_rect = QRectF(center - hub_r, center - hub_r, hub_r * 2, hub_r * 2)

        hub_grad = QRadialGradient(QPointF(center - hub_r * 0.35, center - hub_r * 0.35), hub_r * 1.35)
        hub_grad.setColorAt(0.0, QColor(65, 72, 95, 225))
        hub_grad.setColorAt(0.45, QColor(20, 24, 34, 238))
        hub_grad.setColorAt(1.0, QColor(11, 13, 19, 248))

        hub_rim = QLinearGradient(center - hub_r, center - hub_r, center + hub_r, center + hub_r)
        hub_rim.setColorAt(0.0, QColor(255, 255, 255, 195))
        hub_rim.setColorAt(0.5, QColor(accent_color.red(), accent_color.green(), accent_color.blue(), 175))
        hub_rim.setColorAt(1.0, QColor(255, 255, 255, 55))

        painter.setBrush(QBrush(hub_grad))
        painter.setPen(QPen(QBrush(hub_rim), 1.8))
        painter.drawEllipse(hub_rect)

        lens_rect = QRectF(center - hub_r * 0.78, center - hub_r * 0.82, hub_r * 1.56, hub_r * 0.95)
        lens_grad = QLinearGradient(center, lens_rect.top(), center, lens_rect.bottom())
        lens_grad.setColorAt(0.0, QColor(255, 255, 255, 65))
        lens_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(lens_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(lens_rect)

        if self.hovered_index != -1 and self.hovered_index < len(targets):
            active_label = targets[self.hovered_index]
            VectorIconEngine.draw(
                painter, active_label, QPointF(center, center - 11),
                size=22.0, color=accent_color.lighter(135)
            )
            painter.setPen(QColor(255, 255, 255, 245))
            hub_font = QFont("Inter", 8, QFont.Weight.Bold)
            hub_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.8)
            painter.setFont(hub_font)
            painter.drawText(QRectF(center - hub_r, center + 6, hub_r * 2, 18), Qt.AlignmentFlag.AlignCenter, active_label)
        else:
            pill_rect = QRectF(center - 26, center - 20, 52, 16)
            painter.setBrush(QColor(accent_color.red(), accent_color.green(), accent_color.blue(), 60))
            painter.setPen(QPen(QColor(accent_color.red(), accent_color.green(), accent_color.blue(), 170), 1.0))
            painter.drawRoundedRect(pill_rect, 8, 8)

            pill_font = QFont("Inter", 7, QFont.Weight.Bold)
            pill_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.8)
            painter.setFont(pill_font)
            painter.setPen(QColor(255, 255, 255, 235))
            painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, mod_key)

            title_font = QFont("Inter", 8, QFont.Weight.Bold)
            title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.1)
            painter.setFont(title_font)
            painter.setPen(QColor(225, 230, 240, 235))
            painter.drawText(QRectF(center - hub_r, center + 1, hub_r * 2, 20), Qt.AlignmentFlag.AlignCenter, mode_title)

        painter.restore()