from pathlib import Path
from PIL import Image


class ImageWorker:
    @staticmethod
    def convert(src: Path, dst: Path, target_format: str) -> Path:
        with Image.open(src) as img:
            fmt = "JPEG" if target_format in ("JPG", "JPEG") else target_format
            if fmt in ("JPEG", "PDF", "BMP") and img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(dst, format=fmt, quality=92)
        return dst

    @staticmethod
    def compress(src: Path, dst: Path, quality: int = 60) -> Path:
        with Image.open(src) as img:
            fmt = "JPEG" if src.suffix.lower() in (".jpg", ".jpeg") else "WEBP"
            if fmt == "JPEG" and img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(dst, format=fmt, quality=quality, optimize=True)
        return dst

    @staticmethod
    def resize_half(src: Path, dst: Path) -> Path:
        with Image.open(src) as img:
            new_w = max(1, img.width // 2)
            new_h = max(1, img.height // 2)
            resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            resized.save(dst, quality=92)
        return dst