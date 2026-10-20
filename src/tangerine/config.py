from dataclasses import dataclass, field


@dataclass(frozen=True)
class AppConfig:
    APP_NAME: str = "Open-Tangerine Linux"
    VERSION: str = "2.1.0"

    # Expanded Canvas for Soft Ambient Glow & Hover Expansion
    WINDOW_SIZE: int = 440
    OUTER_RADIUS: int = 162
    INNER_RADIUS: int = 62
    SLICE_GAP_DEG: float = 2.2  # Crisp gap between glass segments

    # Legacy fallback target list
    TARGETS: tuple[str, ...] = ("PNG", "JPG", "WEBP", "PDF", "MP4", "MP3")

    # Wheel Modes & Slices
    WHEELS: dict[str, tuple[str, ...]] = field(default_factory=lambda: {
        "CONVERT": ("PNG", "JPG", "WEBP", "PDF", "MP4", "MP3", "EPUB", "DOCX"),
        "TOOLS": ("COMPRESS", "MERGE", "SPLIT", "RESIZE", "TRIM", "EXTRACT"),
        "ACTIONS": ("FLOAT", "COPY PATH", "TERMINAL", "COPY", "MOVE", "SHARE")
    })

    # File Extensions
    IMAGE_EXTS: frozenset[str] = frozenset({
        ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".gif", ".heic", ".avif"
    })
    MEDIA_EXTS: frozenset[str] = frozenset({
        ".mp4", ".mov", ".mkv", ".avi", ".webm", ".wmv",
        ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".opus"
    })
    DOC_EXTS: frozenset[str] = frozenset({
        ".pdf", ".docx", ".pages", ".pptx", ".xlsx", ".epub", ".txt", ".md"
    })

    # Legacy RGBA fallbacks
    COLOR_ACCENT: tuple[int, int, int, int] = (255, 132, 24, 240)
    COLOR_ACCENT_BORDER: tuple[int, int, int, int] = (255, 225, 180, 255)
    COLOR_DARK_GLASS: tuple[int, int, int, int] = (24, 26, 34, 155)
    COLOR_DARK_BORDER: tuple[int, int, int, int] = (255, 255, 255, 65)
    COLOR_HUB_BG: tuple[int, int, int, int] = (18, 20, 28, 215)


CONFIG = AppConfig()