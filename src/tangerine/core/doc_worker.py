import re
import csv
import json
import hashlib
from pathlib import Path
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtGui import QImage, QPainter, QPageSize
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtPrintSupport import QPrinter


class DocWorker:
    @staticmethod
    def convert_subtitle(src: Path, dst: Path, target_fmt: str) -> Path:
        content = src.read_text(encoding="utf-8", errors="replace")
        if target_fmt == "VTT":
            vtt_body = re.sub(r"(\d{2}:\d{2}:\d{2}),(\d{3})", r"\1.\2", content)
            if not vtt_body.startswith("WEBVTT"):
                vtt_body = "WEBVTT\n\n" + vtt_body
            dst.write_text(vtt_body, encoding="utf-8")
        elif target_fmt == "SRT":
            lines = [line for line in content.splitlines() if not line.startswith("WEBVTT")]
            srt_body = re.sub(r"(\d{2}:\d{2}:\d{2})\.(\d{3})", r"\1,\2", "\n".join(lines).strip())
            dst.write_text(srt_body + "\n", encoding="utf-8")
        elif target_fmt == "TXT":
            cleaned = []
            for line in content.splitlines():
                line_s = line.strip()
                if not line_s or line_s.isdigit() or "-->" in line_s or line_s.startswith("WEBVTT"):
                    continue
                cleaned.append(line_s)
            dst.write_text("\n".join(cleaned), encoding="utf-8")
        return dst

    @staticmethod
    def convert_data(src: Path, dst: Path, target_fmt: str) -> Path:
        if target_fmt == "JSON" and src.suffix.lower() == ".csv":
            with open(src, mode="r", encoding="utf-8", newline="") as f:
                reader = list(csv.DictReader(f))
            dst.write_text(json.dumps(reader, indent=2, ensure_ascii=False), encoding="utf-8")
        elif target_fmt == "CSV" and src.suffix.lower() == ".json":
            data = json.loads(src.read_text(encoding="utf-8"))
            if isinstance(data, list) and data and isinstance(data[0], dict):
                with open(dst, mode="w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
                    writer.writeheader()
                    writer.writerows(data)
        return dst

    @staticmethod
    def render_svg(src: Path, dst: Path, target_fmt: str) -> Path:
        renderer = QSvgRenderer(str(src))
        default_size = renderer.defaultSize()
        w = max(512, default_size.width())
        h = max(512, default_size.height())

        if target_fmt == "PDF":
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(str(dst))
            # QPageSize(QSize) automatically uses Point units in PyQt6
            printer.setPageSize(QPageSize(QSize(w, h)))
            painter = QPainter(printer)
            renderer.render(painter)
            painter.end()
        else:
            image = QImage(w, h, QImage.Format.Format_ARGB32)
            image.fill(Qt.GlobalColor.transparent)
            painter = QPainter(image)
            renderer.render(painter)
            painter.end()
            image.save(str(dst))
        return dst

    @staticmethod
    def compute_sha256(src: Path) -> str:
        h = hashlib.sha256()
        with open(src, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()