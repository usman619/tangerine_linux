import importlib
from pathlib import Path
from PIL import Image, ImageOps

# Dynamically register optional HEIC/AVIF support if installed in venv
try:
    _heif = importlib.import_module("pillow_heif")
    _heif.register_heif_opener()
except ModuleNotFoundError:
    pass


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
    def compress(src: Path, dst: Path, quality: int = 65) -> Path:
        with Image.open(src) as img:
            fmt = "JPEG" if src.suffix.lower() in (".jpg", ".jpeg") else "WEBP"
            if fmt == "JPEG" and img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(dst, format=fmt, quality=quality, optimize=True)
        return dst

    @staticmethod
    def transform(src: Path, dst: Path, scale_pct: int = 50, rotate_deg: int = 0) -> Path:
        with Image.open(src) as img:
            out_img: Image.Image = img
            if rotate_deg:
                out_img = out_img.rotate(-rotate_deg, expand=True)
            if scale_pct != 100:
                new_w = max(1, int(out_img.width * (scale_pct / 100.0)))
                new_h = max(1, int(out_img.height * (scale_pct / 100.0)))
                out_img = out_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            out_img.save(dst, quality=92)
        return dst

    @staticmethod
    def strip_exif(src: Path, dst: Path) -> Path:
        with Image.open(src) as img:
            # Apply orientation before stripping EXIF so rotated phone photos stay upright
            transposed = ImageOps.exif_transpose(img)
            source_img = transposed if transposed is not None else img
            # Copy raw pixel buffer without copying metadata dictionary
            clean = source_img.copy()
            clean.info.clear()
            clean.save(dst, quality=95, exif=b"")
        return dst