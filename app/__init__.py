# App module - UI controllers

from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap

# Icon folder at project root
ICON_DIR = Path(__file__).parent.parent / "Icon"


def load_icon(filename: str) -> QIcon:
    """
    Load an icon from the Icon/ folder, scaling large images down
    so they work as window icons.

    Args:
        filename: Icon file name, e.g. "app.ico" or "app.png"

    Returns:
        QIcon (empty if file not found)
    """
    icon_path = ICON_DIR / filename
    if icon_path.exists():
        pixmap = QPixmap(str(icon_path))
        if not pixmap.isNull():
            # Build a multi-size icon for best display at any DPI
            icon = QIcon()
            for size in (16, 32, 48, 64):
                scaled = pixmap.scaled(
                    size, size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                icon.addPixmap(scaled)
            return icon
    return QIcon()
