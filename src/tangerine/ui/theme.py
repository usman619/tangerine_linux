from dataclasses import dataclass
from PyQt6.QtGui import QColor


@dataclass(frozen=True)
class DesignTokens:
    # Surface Elevation (Dark Theme Parity)
    BG_BASE: str = "#0B0D13"
    BG_SURFACE: str = "#12151E"
    BG_ELEVATED: str = "#1A1E2B"
    BG_GLASS: str = "rgba(22, 26, 38, 215)"

    # Borders & Dividers
    BORDER_SUBTLE: str = "#262B3D"
    BORDER_FOCUS: str = "#FF7E14"

    # Typography
    TEXT_PRIMARY: str = "#F3F4F6"
    TEXT_SECONDARY: str = "#9CA3AF"
    TEXT_MUTED: str = "#6B7280"

    # Brand & Mode Accents
    ACCENT_CONVERT: str = "#FF7E14"   # Tangerine Orange
    ACCENT_TOOLS: str = "#0EA5E9"     # Sky Cyan
    ACCENT_ACTIONS: str = "#8B5CF6"   # Violet
    SUCCESS: str = "#10B981"
    DANGER: str = "#EF4444"

    # 4px Grid Spacing & Radii
    SPACE_1: int = 4
    SPACE_2: int = 8
    SPACE_3: int = 12
    SPACE_4: int = 16
    SPACE_6: int = 24
    RADIUS_SM: int = 6
    RADIUS_MD: int = 10
    RADIUS_LG: int = 14


TOKENS = DesignTokens()


def get_app_stylesheet() -> str:
    """Reusable QSS pattern following pyqt6-ui-designer guidelines."""
    return f"""
    QDialog, QWidget#SurfaceCard {{
        background-color: {TOKENS.BG_SURFACE};
        color: {TOKENS.TEXT_PRIMARY};
        font-family: 'Inter', 'Cantarell', 'Segoe UI', sans-serif;
        font-size: 13px;
    }}
    QFrame#Card {{
        background-color: {TOKENS.BG_ELEVATED};
        border: 1px solid {TOKENS.BORDER_SUBTLE};
        border-radius: {TOKENS.RADIUS_MD}px;
        padding: {TOKENS.SPACE_3}px;
    }}
    QLabel {{
        color: {TOKENS.TEXT_PRIMARY};
        background: transparent;
    }}
    QLabel#MutedLabel {{
        color: {TOKENS.TEXT_SECONDARY};
        font-size: 12px;
    }}
    QLabel#HeadingLabel {{
        color: {TOKENS.TEXT_PRIMARY};
        font-size: 15px;
        font-weight: 600;
    }}
    QPushButton {{
        background-color: {TOKENS.BG_ELEVATED};
        color: {TOKENS.TEXT_PRIMARY};
        border: 1px solid {TOKENS.BORDER_SUBTLE};
        border-radius: {TOKENS.RADIUS_SM}px;
        padding: 6px 14px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: #232838;
        border-color: #3B425B;
    }}
    QPushButton:pressed {{
        background-color: #161924;
    }}
    QPushButton#PrimaryButton {{
        background-color: {TOKENS.ACCENT_CONVERT};
        color: #FFFFFF;
        border: 1px solid #FF9844;
        font-weight: 600;
    }}
    QPushButton#PrimaryButton:hover {{
        background-color: #FF8F33;
    }}
    QPushButton#PrimaryButton:pressed {{
        background-color: #E06600;
    }}
    QSlider::groove:horizontal {{
        border: 1px solid {TOKENS.BORDER_SUBTLE};
        height: 6px;
        background: {TOKENS.BG_BASE};
        border-radius: 3px;
    }}
    QSlider::sub-page:horizontal {{
        background: {TOKENS.ACCENT_CONVERT};
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background: #FFFFFF;
        border: 2px solid {TOKENS.ACCENT_CONVERT};
        width: 14px;
        height: 14px;
        margin: -5px 0;
        border-radius: 8px;
    }}
    QSpinBox, QComboBox, QLineEdit {{
        background-color: {TOKENS.BG_BASE};
        color: {TOKENS.TEXT_PRIMARY};
        border: 1px solid {TOKENS.BORDER_SUBTLE};
        border-radius: {TOKENS.RADIUS_SM}px;
        padding: 5px 8px;
    }}
    QSpinBox:focus, QComboBox:focus, QLineEdit:focus {{
        border: 1px solid {TOKENS.BORDER_FOCUS};
    }}
    QMenu {{
        background-color: {TOKENS.BG_SURFACE};
        color: {TOKENS.TEXT_PRIMARY};
        border: 1px solid {TOKENS.BORDER_SUBTLE};
        border-radius: {TOKENS.RADIUS_SM}px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 20px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {TOKENS.ACCENT_CONVERT};
        color: #FFFFFF;
    }}
    """