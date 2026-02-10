"""File type classification based on extension and MIME type."""

from pathlib import Path
from typing import Optional


# Category definitions with file extensions
CATEGORIES = {
    "Photos": {"jpg", "jpeg", "png", "heic", "webp", "gif", "bmp", "tiff", "tif", "raw", "cr2", "nef"},
    "Videos": {"mp4", "mkv", "mov", "avi", "webm", "wmv", "flv", "m4v", "3gp"},
    "Audio": {"mp3", "wav", "flac", "m4a", "aac", "ogg", "wma", "aiff"},
    "Documents": {"pdf", "docx", "doc", "xlsx", "xls", "pptx", "ppt", "txt", "rtf", "odt", "ods", "odp"},
    "Archives": {"zip", "rar", "7z", "tar", "gz", "bz2", "xz", "tgz"},
    "Installers": {"exe", "msi", "dmg", "pkg", "deb", "rpm", "appimage"},
}

# Build reverse lookup from extension to category
EXTENSION_TO_CATEGORY = {}
for category, extensions in CATEGORIES.items():
    for ext in extensions:
        EXTENSION_TO_CATEGORY[ext.lower()] = category

# MIME type to category mapping (for cases where extension is ambiguous)
MIME_TO_CATEGORY = {
    # Photos
    "image/jpeg": "Photos",
    "image/png": "Photos",
    "image/gif": "Photos",
    "image/webp": "Photos",
    "image/heic": "Photos",
    "image/heif": "Photos",
    "image/bmp": "Photos",
    "image/tiff": "Photos",

    # Videos
    "video/mp4": "Videos",
    "video/x-matroska": "Videos",
    "video/quicktime": "Videos",
    "video/x-msvideo": "Videos",
    "video/webm": "Videos",
    "video/x-ms-wmv": "Videos",
    "video/x-flv": "Videos",

    # Audio
    "audio/mpeg": "Audio",
    "audio/mp3": "Audio",
    "audio/wav": "Audio",
    "audio/x-wav": "Audio",
    "audio/flac": "Audio",
    "audio/x-flac": "Audio",
    "audio/mp4": "Audio",
    "audio/aac": "Audio",
    "audio/ogg": "Audio",

    # Documents
    "application/pdf": "Documents",
    "application/msword": "Documents",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Documents",
    "application/vnd.ms-excel": "Documents",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Documents",
    "application/vnd.ms-powerpoint": "Documents",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "Documents",
    "text/plain": "Documents",

    # Google Docs (exported as Office formats)
    "application/vnd.google-apps.document": "Documents",
    "application/vnd.google-apps.spreadsheet": "Documents",
    "application/vnd.google-apps.presentation": "Documents",

    # Archives
    "application/zip": "Archives",
    "application/x-rar-compressed": "Archives",
    "application/x-7z-compressed": "Archives",
    "application/x-tar": "Archives",
    "application/gzip": "Archives",

    # Installers
    "application/x-msdownload": "Installers",
    "application/x-msi": "Installers",
}


def classify_file(filename: str, mime_type: Optional[str] = None) -> str:
    """
    Classify a file into a category based on its extension and MIME type.

    Args:
        filename: The file name (with extension)
        mime_type: Optional MIME type for more accurate classification

    Returns:
        Category name (Photos, Videos, Audio, Documents, Archives, Installers, or Other)
    """
    # First try MIME type if provided
    if mime_type:
        category = MIME_TO_CATEGORY.get(mime_type)
        if category:
            return category

    # Fall back to extension
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext:
        category = EXTENSION_TO_CATEGORY.get(ext)
        if category:
            return category

    return "Other"


def get_category_icon(category: str) -> str:
    """Get an emoji icon for a category."""
    icons = {
        "Photos": "📷",
        "Videos": "🎬",
        "Audio": "🎵",
        "Documents": "📄",
        "Archives": "📦",
        "Installers": "💿",
        "Other": "📁",
    }
    return icons.get(category, "📁")


def get_all_categories() -> list:
    """Get list of all category names."""
    return list(CATEGORIES.keys()) + ["Other"]
