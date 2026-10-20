from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    APP_NAME: str = "Open-Tangerine Linux"
    VERSION: str = "3.0.0"

    WINDOW_SIZE: int = 440
    OUTER_RADIUS: int = 164
    INNER_RADIUS: int = 62
    SLICE_GAP_DEG: float = 2.2

    IMAGE_EXTS: frozenset[str] = frozenset({
        ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".gif", ".heic", ".avif", ".svg"
    })
    VIDEO_EXTS: frozenset[str] = frozenset({
        ".mp4", ".mov", ".mkv", ".avi", ".webm", ".wmv"
    })
    AUDIO_EXTS: frozenset[str] = frozenset({
        ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".opus"
    })
    SUBTITLE_EXTS: frozenset[str] = frozenset({".srt", ".vtt"})
    DATA_EXTS: frozenset[str] = frozenset({".csv", ".json"})
    DOC_EXTS: frozenset[str] = frozenset({
        ".pdf", ".docx", ".pages", ".pptx", ".xlsx", ".epub", ".txt", ".md"
    })

    @property
    def MEDIA_EXTS(self) -> frozenset[str]:
        return self.VIDEO_EXTS | self.AUDIO_EXTS

    # Default Fallback Wheels (before a file enters the drop zone)
    WHEELS: dict[str, tuple[str, ...]] = field(default_factory=lambda: {
        "CONVERT": ("PNG", "JPG", "WEBP", "PDF", "MP4", "MP3"),
        "TOOLS": ("COMPRESS", "MERGE", "SPLIT", "RESIZE", "TRIM", "EXTRACT"),
        "ACTIONS": ("FLOAT", "COPY PATH", "TERMINAL", "SHA256", "COPY", "MOVE", "SHARE")
    })

    def get_contextual_slices(self, mode: str, file_paths: list[str]) -> tuple[str, ...]:
        """Filters wheel slices dynamically so only valid actions for the dragged files appear."""
        if not file_paths:
            return self.WHEELS.get(mode, self.WHEELS["CONVERT"])

        exts = {Path(p).suffix.lower() for p in file_paths if Path(p).suffix}
        count = len(file_paths)

        is_all_img = bool(exts) and exts.issubset(self.IMAGE_EXTS)
        is_all_vid = bool(exts) and exts.issubset(self.VIDEO_EXTS)
        is_all_aud = bool(exts) and exts.issubset(self.AUDIO_EXTS)
        is_all_pdf = exts == {".pdf"}
        is_all_sub = bool(exts) and exts.issubset(self.SUBTITLE_EXTS)
        is_all_data = bool(exts) and exts.issubset(self.DATA_EXTS)
        is_all_zip = exts == {".zip"}

        # 1. CONTEXTUAL CONVERT WHEEL (SHIFT)
        if mode == "CONVERT":
            if is_all_img:
                candidates = ["PNG", "JPG", "WEBP", "PDF", "AVIF"]
                # Remove the format if dragging a single image of that exact format
                if count == 1:
                    single_ext = next(iter(exts)).lstrip(".").upper()
                    if single_ext == "JPEG":
                        single_ext = "JPG"
                    candidates = [c for c in candidates if c != single_ext]
                return tuple(candidates)
            if is_all_vid:
                return ("MP4", "WEBM", "GIF", "MP3", "WAV")
            if is_all_aud:
                return ("MP3", "WAV", "FLAC", "OGG")
            if is_all_pdf:
                return ("PNG", "TXT", "DOCX")
            if is_all_sub:
                return ("VTT", "TXT") if exts == {".srt"} else ("SRT", "TXT")
            if is_all_data:
                return ("JSON",) if exts == {".csv"} else ("CSV",)
            return ("PDF", "DOCX", "EPUB", "TXT")

        # 2. CONTEXTUAL TOOLS WHEEL (ALT)
        if mode == "TOOLS":
            if is_all_img:
                tools = ["COMPRESS", "RESIZE", "CLEAN EXIF"]
                if count > 1:
                    tools.insert(0, "MERGE")
                return tuple(tools)
            if is_all_vid:
                return ("COMPRESS", "TRIM", "EXTRACT")
            if is_all_aud:
                return ("TRIM", "COMPRESS")
            if is_all_pdf:
                tools = ["SPLIT", "EXTRACT"]
                if count > 1:
                    tools.insert(0, "MERGE")
                return tuple(tools)
            if is_all_zip:
                return ("EXTRACT",)
            return ("EXTRACT",)

        # 3. CONTEXTUAL ACTIONS WHEEL (CTRL)
        return ("FLOAT", "COPY PATH", "TERMINAL", "SHA256", "COPY", "MOVE", "SHARE")


CONFIG = AppConfig()