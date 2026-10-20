import math
import threading
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QFont, QCursor,
    QPainterPath, QLinearGradient, QRadialGradient, QBrush
)

from tangerine.config import CONFIG
from tangerine.core.dispatcher import ConversionDispatcher
from tangerine.core.action_worker import ActionWorker


class RadialDropOverlay(QWidget):
    action_completed = pyqtSignal(list)

    MODE_META = {
        "CONVERT": ("CONVERT", "SHIFT", QColor(255, 136, 28)),   # Tangerine Orange
        "TOOLS":   ("TOOLBOX", "ALT",   QColor(56, 189, 248)),   # Liquid Cyan
        "ACTIONS": ("ACTIONS", "CTRL",  QColor(168, 85, 247)),   # Amethyst Glass
    }

    SLICE_ICONS = {
        "PNG": "🖼", "JPG": "📷", "WEBP": "🌐", "PDF": "📄",
        "MP4": "🎬", "MP3": "🎵", "EPUB": "📖", "DOCX": "📝",
        "COMPRESS": "⚡", "MERGE": "🔗", "SPLIT": "✂",
        "RESIZE": "📐", "TRIM": "⏱", "EXTRACT": "📤",
        "FLOAT": "🪟", "COPY PATH": "📋", "TERMINAL": "❯_",
        "COPY": "📑", "MOVE": "📦", "SHARE": "🗜",
    }

    def __init__(self):
        super().__init__()
        self.current_mode = "CONVERT"
        self.hovered_index = -1

        # 60 FPS Animation States
        self._open_progress = 0.0
        self._hover_weights: list[float] = [0.0] * 12

        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)  # ~60 FPS
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

    def summon(self, mode: str = "CONVERT") -> None:
        was_visible = self.isVisible()
        self.current_mode = mode
        targets = self._get_targets()

        if len(self._hover_weights) != len(targets):
            self._hover_weights = [0.0] * len(targets)

        if not was_visible:
            pos = QCursor.pos()
            half = CONFIG.WINDOW_SIZE // 2
            self.move(pos.x() - half, pos.y() - half)
            self.hovered_index = -1
            self._open_progress = 0.25
            self._hover_weights = [0.0] * len(targets)
            self.show()
            self.raise_()

        if not self._anim_timer.isActive():
            self._anim_timer.start()
        self.update()

    def hideEvent(self, event) -> None:
        self._anim_timer.stop()
        super().hideEvent(event)

    def _tick_animation(self) -> None:
        needs_repaint = False

        # Smooth spring pop-in animation
        if self._open_progress < 1.0:
            self._open_progress = min(1.0, self._open_progress + (1.0 - self._open_progress) * 0.28 + 0.02)
            needs_repaint = True

        # Per-slice smooth liquid expansion
        targets = self._get_targets()
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

    def _get_targets(self) -> tuple[str, ...]:
        return CONFIG.WHEELS.get(self.current_mode, CONFIG.WHEELS["CONVERT"])

    def _get_sector_at(self, pos: QPoint) -> int:
        targets = self._get_targets()
        center = CONFIG.WINDOW_SIZE / 2
        dx, dy = pos.x() - center, pos.y() - center
        dist = math.hypot(dx, dy)

        if dist < CONFIG.INNER_RADIUS - 6 or dist > CONFIG.OUTER_RADIUS + 22:
            return -1

        angle = math.degrees(math.atan2(dy, dx)) % 360
        span = 360 / len(targets)
        return int(angle // span)

    # --- Drag & Drop Events ---
    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
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
        self.hide()
        if idx == -1:
            return

        targets = self._get_targets()
        target_action = targets[idx]
        file_paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]

        if not file_paths:
            return

        event.accept()

        if self.current_mode == "ACTIONS" and target_action in ("FLOAT", "COPY", "MOVE"):
            if target_action == "FLOAT":
                msg = ActionWorker.float_files(file_paths)
            elif target_action == "COPY":
                msg = ActionWorker.copy_or_move_files(file_paths, move=False)
            else:
                msg = ActionWorker.copy_or_move_files(file_paths, move=True)
            self.action_completed.emit([msg])
            return

        threading.Thread(
            target=self._run_dispatch,
            args=(file_paths, self.current_mode, target_action),
            daemon=True
        ).start()

    def _run_dispatch(self, file_paths: list[str], mode: str, target: str) -> None:
        outputs = ConversionDispatcher.dispatch(file_paths, mode, target)
        if outputs:
            self.action_completed.emit(outputs)

    # ==========================================================
    # LIQUID GLASS RENDERING PIPELINE
    # ==========================================================
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        center = CONFIG.WINDOW_SIZE / 2
        center_pt = QPointF(center, center)
        targets = self._get_targets()
        num_slices = len(targets)
        span = 360.0 / num_slices
        gap = CONFIG.SLICE_GAP_DEG

        mode_title, mod_key, accent_color = self.MODE_META.get(
            self.current_mode, ("CONVERT", "SHIFT", QColor(255, 136, 28))
        )

        # Apply smooth pop-in scale transform around center
        scale = 0.82 + 0.18 * self._open_progress
        painter.save()
        painter.translate(center, center)
        painter.scale(scale, scale)
        painter.translate(-center, -center)

        # ------------------------------------------------------
        # LAYER 1: Ambient Soft Shadow + Frosted Base Torus Ring
        # ------------------------------------------------------
        ambient_glow = QRadialGradient(center_pt, CONFIG.OUTER_RADIUS + 34)
        ambient_glow.setColorAt(0.0, QColor(0, 0, 0, 0))
        ambient_glow.setColorAt(0.32, QColor(8, 10, 16, 115))
        ambient_glow.setColorAt(0.76, QColor(8, 10, 18, 145))
        ambient_glow.setColorAt(0.90, QColor(accent_color.red(), accent_color.green(), accent_color.blue(), 32))
        ambient_glow.setColorAt(1.0, QColor(0, 0, 0, 0))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(ambient_glow))
        painter.drawEllipse(center_pt, CONFIG.OUTER_RADIUS + 34, CONFIG.OUTER_RADIUS + 34)

        # Outer continuous glass casing ring
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
        casing_grad.setColorAt(0.0, QColor(255, 255, 255, 38))
        casing_grad.setColorAt(0.45, QColor(22, 25, 36, 145))
        casing_grad.setColorAt(1.0, QColor(12, 14, 22, 185))

        rim_grad = QLinearGradient(
            center - casing_outer, center - casing_outer,
            center + casing_outer, center + casing_outer
        )
        rim_grad.setColorAt(0.0, QColor(255, 255, 255, 110))
        rim_grad.setColorAt(0.5, QColor(255, 255, 255, 25))
        rim_grad.setColorAt(1.0, QColor(255, 255, 255, 55))

        painter.setBrush(QBrush(casing_grad))
        painter.setPen(QPen(QBrush(rim_grad), 1.2))
        painter.drawPath(casing_path)

        # ------------------------------------------------------
        # LAYER 2: Individual Liquid Glass Slices
        # ------------------------------------------------------
        for i, label in enumerate(targets):
            weight = self._hover_weights[i] if i < len(self._hover_weights) else 0.0

            # Dynamic radius expansion & slight inner lift on hover
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

            # Compute slice bounding coordinates for directional glass sheen
            mid_rad = math.radians(start_deg + slice_span / 2.0)
            mid_r = (r_in + r_out) / 2.0
            sx = center + mid_r * math.cos(mid_rad)
            sy = center + mid_r * math.sin(mid_rad)

            # Base frosted glass fill mixed with liquid accent glow on hover
            glass_grad = QLinearGradient(sx - 45, sy - 45, sx + 45, sy + 45)
            if weight > 0.01:
                # Blend between smoky glass and luminous refractive liquid accent
                ar, ag, ab = accent_color.red(), accent_color.green(), accent_color.blue()
                top_r = int(55 + (min(255, ar + 45) - 55) * weight)
                top_g = int(60 + (min(255, ag + 45) - 60) * weight)
                top_b = int(75 + (min(255, ab + 45) - 75) * weight)
                top_a = int(165 + 75 * weight)

                bot_r = int(24 + (ar - 24) * weight)
                bot_g = int(26 + (ag - 26) * weight)
                bot_b = int(36 + (ab - 36) * weight)
                bot_a = int(175 + 65 * weight)

                glass_grad.setColorAt(0.0, QColor(255, 255, 255, int(90 + 115 * weight)))
                glass_grad.setColorAt(0.22, QColor(top_r, top_g, top_b, top_a))
                glass_grad.setColorAt(1.0, QColor(bot_r, bot_g, bot_b, bot_a))
            else:
                glass_grad.setColorAt(0.0, QColor(255, 255, 255, 62))
                glass_grad.setColorAt(0.25, QColor(38, 42, 56, 155))
                glass_grad.setColorAt(1.0, QColor(18, 20, 28, 175))

            # Specular Glass Rim Border (bright top-left reflection, subtle bottom-right)
            border_grad = QLinearGradient(sx - 50, sy - 50, sx + 50, sy + 50)
            border_grad.setColorAt(0.0, QColor(255, 255, 255, int(135 + 115 * weight)))
            border_grad.setColorAt(0.5, QColor(
                accent_color.red(), accent_color.green(), accent_color.blue(), int(45 + 160 * weight)
            ))
            border_grad.setColorAt(1.0, QColor(255, 255, 255, int(30 + 70 * weight)))

            painter.setBrush(QBrush(glass_grad))
            painter.setPen(QPen(QBrush(border_grad), 1.3 + 1.1 * weight))
            painter.drawPath(path)

            # Inner Specular Glint along outer arc
            if weight > 0.15:
                glow_rect = QRectF(center - (r_out - 3), center - (r_out - 3), (r_out - 3) * 2, (r_out - 3) * 2)
                glint_path = QPainterPath()
                glint_path.arcMoveTo(glow_rect, qt_start - 4)
                glint_path.arcTo(glow_rect, qt_start - 4, -(slice_span - 8))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(QColor(255, 255, 255, int(150 * weight)), 1.6))
                painter.drawPath(glint_path)

            # --------------------------------------------------
            # LAYER 3: Slice Icon & Crisp Label
            # --------------------------------------------------
            icon_char = self.SLICE_ICONS.get(label, "•")
            painter.setPen(QColor(255, 255, 255, int(185 + 70 * weight)))
            icon_font = QFont("Sans Serif", 11)
            painter.setFont(icon_font)
            painter.drawText(
                QRectF(sx - 44, sy - 21, 88, 20),
                Qt.AlignmentFlag.AlignCenter,
                icon_char
            )

            # Label text with subtle dark drop-shadow for legibility over bright wallpapers
            label_font = QFont("Sans Serif", 9, QFont.Weight.Bold)
            label_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.6)
            painter.setFont(label_font)

            painter.setPen(QColor(0, 0, 0, 150))
            painter.drawText(
                QRectF(sx - 43, sy - 1, 88, 22),
                Qt.AlignmentFlag.AlignCenter,
                label
            )

            painter.setPen(QColor(255, 255, 255, int(220 + 35 * weight)))
            painter.drawText(
                QRectF(sx - 44, sy - 2, 88, 22),
                Qt.AlignmentFlag.AlignCenter,
                label
            )

        # ------------------------------------------------------
        # LAYER 4: Central Liquid Glass Orb (Core Hub)
        # ------------------------------------------------------
        hub_r = CONFIG.INNER_RADIUS - 8
        hub_rect = QRectF(center - hub_r, center - hub_r, hub_r * 2, hub_r * 2)

        hub_grad = QRadialGradient(
            QPointF(center - hub_r * 0.35, center - hub_r * 0.35),
            hub_r * 1.35
        )
        hub_grad.setColorAt(0.0, QColor(75, 82, 105, 215))
        hub_grad.setColorAt(0.45, QColor(24, 27, 38, 230))
        hub_grad.setColorAt(1.0, QColor(12, 14, 20, 245))

        hub_rim = QLinearGradient(
            center - hub_r, center - hub_r,
            center + hub_r, center + hub_r
        )
        hub_rim.setColorAt(0.0, QColor(255, 255, 255, 190))
        hub_rim.setColorAt(0.5, QColor(accent_color.red(), accent_color.green(), accent_color.blue(), 165))
        hub_rim.setColorAt(1.0, QColor(255, 255, 255, 50))

        painter.setBrush(QBrush(hub_grad))
        painter.setPen(QPen(QBrush(hub_rim), 2.0))
        painter.drawEllipse(hub_rect)

        # Top-half glass lens reflection arc inside the orb
        lens_rect = QRectF(center - hub_r * 0.78, center - hub_r * 0.82, hub_r * 1.56, hub_r * 0.95)
        lens_grad = QLinearGradient(center, lens_rect.top(), center, lens_rect.bottom())
        lens_grad.setColorAt(0.0, QColor(255, 255, 255, 70))
        lens_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(lens_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(lens_rect)

        # Center Hub Typography (Shows hovered target or active mode + modifier pill)
        if self.hovered_index != -1:
            active_label = targets[self.hovered_index]
            active_icon = self.SLICE_ICONS.get(active_label, "🍊")

            painter.setPen(QColor(255, 255, 255, 240))
            painter.setFont(QFont("Sans Serif", 14))
            painter.drawText(
                QRectF(center - hub_r, center - 24, hub_r * 2, 24),
                Qt.AlignmentFlag.AlignCenter,
                active_icon
            )

            painter.setPen(accent_color.lighter(135))
            hub_font = QFont("Sans Serif", 9, QFont.Weight.Bold)
            hub_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.8)
            painter.setFont(hub_font)
            painter.drawText(
                QRectF(center - hub_r, center + 2, hub_r * 2, 20),
                Qt.AlignmentFlag.AlignCenter,
                active_label
            )
        else:
            # Modifier Badge Pill ("SHIFT", "ALT", "CTRL")
            pill_rect = QRectF(center - 26, center - 20, 52, 16)
            painter.setBrush(QColor(accent_color.red(), accent_color.green(), accent_color.blue(), 55))
            painter.setPen(QPen(QColor(accent_color.red(), accent_color.green(), accent_color.blue(), 160), 1.0))
            painter.drawRoundedRect(pill_rect, 8, 8)

            pill_font = QFont("Sans Serif", 7, QFont.Weight.Bold)
            pill_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.8)
            painter.setFont(pill_font)
            painter.setPen(QColor(255, 255, 255, 230))
            painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, mod_key)

            # Mode Title ("CONVERT", "TOOLBOX", "ACTIONS")
            title_font = QFont("Sans Serif", 8, QFont.Weight.Bold)
            title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.1)
            painter.setFont(title_font)
            painter.setPen(QColor(220, 225, 235, 235))
            painter.drawText(
                QRectF(center - hub_r, center + 1, hub_r * 2, 20),
                Qt.AlignmentFlag.AlignCenter,
                mode_title
            )

        painter.restore()