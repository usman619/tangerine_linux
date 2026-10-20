from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QPainterPath, QIcon, QPixmap


class VectorIconEngine:
    """Draws crisp 24x24 normalized vector icons (zero emojis)."""

    @staticmethod
    def draw(painter: QPainter, name: str, center: QPointF, size: float = 20.0, color: QColor = QColor(255, 255, 255)) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        scale = size / 24.0
        painter.translate(center.x() - size / 2.0, center.y() - size / 2.0)
        painter.scale(scale, scale)

        pen = QPen(color, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        n = name.upper()

        if n in ("PNG", "JPG", "WEBP", "SVG", "AVIF", "IMAGE"):
            # Camera / Image Frame Icon
            painter.drawRoundedRect(QRectF(3, 3, 18, 18), 3, 3)
            painter.drawEllipse(QPointF(8.5, 8.5), 1.5, 1.5)
            path = QPainterPath()
            path.moveTo(21, 15)
            path.lineTo(16, 10)
            path.lineTo(5, 21)
            painter.drawPath(path)

        elif n in ("MP4", "WEBM", "MKV", "GIF", "VIDEO"):
            # Film Clapper / Video Frame
            painter.drawRoundedRect(QRectF(2, 4, 20, 16), 2.5, 2.5)
            painter.drawLine(7, 4, 7, 20)
            painter.drawLine(17, 4, 17, 20)
            painter.drawLine(2, 12, 22, 12)
            painter.drawLine(2, 8, 7, 8)
            painter.drawLine(2, 16, 7, 16)
            painter.drawLine(17, 8, 22, 8)
            painter.drawLine(17, 16, 22, 16)

        elif n in ("MP3", "WAV", "FLAC", "AUDIO"):
            # Musical Note / Waveform
            path = QPainterPath()
            path.moveTo(9, 18)
            path.lineTo(9, 5)
            path.lineTo(21, 3)
            path.lineTo(21, 16)
            painter.drawPath(path)
            painter.drawEllipse(QPointF(6, 18), 3, 3)
            painter.drawEllipse(QPointF(18, 16), 3, 3)

        elif n in ("PDF", "DOCX", "EPUB", "TXT", "SRT", "VTT", "CSV", "JSON"):
            # Document Sheet with Folded Corner & Text Lines
            path = QPainterPath()
            path.moveTo(14, 2)
            path.lineTo(6, 2)
            path.quadTo(4, 2, 4, 4)
            path.lineTo(4, 20)
            path.quadTo(4, 22, 6, 22)
            path.lineTo(18, 22)
            path.quadTo(20, 22, 20, 20)
            path.lineTo(20, 8)
            path.closeSubpath()
            painter.drawPath(path)
            fold = QPainterPath()
            fold.moveTo(14, 2)
            fold.lineTo(14, 8)
            fold.lineTo(20, 8)
            painter.drawPath(fold)
            painter.drawLine(8, 13, 16, 13)
            painter.drawLine(8, 17, 13, 17)

        elif n == "COMPRESS":
            # Inward Compression Arrows
            painter.drawLine(4, 14, 10, 14)
            painter.drawLine(10, 14, 10, 20)
            painter.drawLine(3, 21, 10, 14)
            painter.drawLine(20, 10, 14, 10)
            painter.drawLine(14, 10, 14, 4)
            painter.drawLine(21, 3, 14, 10)

        elif n == "MERGE":
            # Stacked Layers / Merge
            poly1 = QPainterPath()
            poly1.moveTo(12, 2)
            poly1.lineTo(2, 7)
            poly1.lineTo(12, 12)
            poly1.lineTo(22, 7)
            poly1.closeSubpath()
            painter.drawPath(poly1)
            painter.drawLine(2, 12, 12, 17)
            painter.drawLine(12, 17, 22, 12)
            painter.drawLine(2, 17, 12, 22)
            painter.drawLine(12, 22, 22, 17)

        elif n in ("SPLIT", "TRIM"):
            # Scissors Icon
            painter.drawEllipse(QPointF(6, 6), 3, 3)
            painter.drawEllipse(QPointF(6, 18), 3, 3)
            painter.drawLine(20, 4, 8, 15)
            painter.drawLine(14, 14, 20, 20)
            painter.drawLine(8, 8, 12, 12)

        elif n == "RESIZE":
            # Maximize / Aspect Frame
            painter.drawLine(15, 3, 21, 3)
            painter.drawLine(21, 3, 21, 9)
            painter.drawLine(9, 21, 3, 21)
            painter.drawLine(3, 21, 3, 15)
            painter.drawLine(21, 3, 14, 10)
            painter.drawLine(3, 21, 10, 14)

        elif n == "EXTRACT":
            # Box with Upward Extract Arrow
            painter.drawLine(12, 3, 12, 15)
            painter.drawLine(7, 8, 12, 3)
            painter.drawLine(17, 8, 12, 3)
            painter.drawLine(4, 15, 4, 19)
            painter.drawLine(4, 19, 20, 19)
            painter.drawLine(20, 19, 20, 15)

        elif n == "CLEAN EXIF":
            # Shield / Privacy Off
            path = QPainterPath()
            path.moveTo(12, 2)
            path.lineTo(4, 5)
            path.lineTo(4, 11)
            path.quadTo(4, 18, 12, 22)
            path.quadTo(20, 18, 20, 11)
            path.lineTo(20, 5)
            path.closeSubpath()
            painter.drawPath(path)
            painter.drawLine(9, 12, 11, 14)
            painter.drawLine(11, 14, 15, 10)

        elif n == "FLOAT":
            # Picture-in-Picture Floating Window
            painter.drawRoundedRect(QRectF(2, 4, 20, 16), 2, 2)
            painter.setBrush(color)
            painter.drawRoundedRect(QRectF(11, 11, 9, 7), 1.5, 1.5)

        elif n == "COPY PATH":
            # Link / Clipboard Path
            painter.drawRoundedRect(QRectF(9, 9, 13, 13), 2, 2)
            path = QPainterPath()
            path.moveTo(5, 15)
            path.lineTo(4, 15)
            path.quadTo(2, 15, 2, 13)
            path.lineTo(2, 4)
            path.quadTo(2, 2, 4, 2)
            path.lineTo(13, 2)
            path.quadTo(15, 2, 15, 4)
            path.lineTo(15, 5)
            painter.drawPath(path)

        elif n == "TERMINAL":
            # Terminal Prompt (>_)
            painter.drawRoundedRect(QRectF(2, 4, 20, 16), 2, 2)
            painter.drawLine(6, 9, 10, 12)
            painter.drawLine(10, 12, 6, 15)
            painter.drawLine(12, 15, 17, 15)

        elif n == "SHA256":
            # Hash (#) Checksum Icon
            painter.drawLine(4, 9, 20, 9)
            painter.drawLine(4, 15, 20, 15)
            painter.drawLine(10, 3, 8, 21)
            painter.drawLine(16, 3, 14, 21)

        elif n in ("COPY", "MOVE", "SHARE"):
            # Folder / Archive Box
            path = QPainterPath()
            path.moveTo(22, 19)
            path.quadTo(22, 21, 20, 21)
            path.lineTo(4, 21)
            path.quadTo(2, 21, 2, 19)
            path.lineTo(2, 5)
            path.quadTo(2, 3, 4, 3)
            path.lineTo(9, 3)
            path.lineTo(11, 6)
            path.lineTo(20, 6)
            path.quadTo(22, 6, 22, 8)
            path.closeSubpath()
            painter.drawPath(path)

        else:
            # Default Tangerine Citrus Emblem
            painter.drawEllipse(QPointF(12, 13), 8, 8)
            painter.drawLine(12, 5, 15, 2)

        painter.restore()

    @classmethod
    def as_qicon(cls, name: str, size: int = 32, color: QColor = QColor(255, 126, 20)) -> QIcon:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        p = QPainter(pixmap)
        cls.draw(p, name, QPointF(size / 2, size / 2), size * 0.75, color)
        p.end()
        return QIcon(pixmap)