"""Local folder organization for archived files."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from core.classifier import classify_file


# Categories that get year/month subfolders
DATE_ORGANIZED_CATEGORIES = {"Photos", "Videos", "Documents"}


def get_local_path(
    archive_root: Path,
    filename: str,
    mime_type: Optional[str] = None,
    modified_date: Optional[datetime] = None
) -> Path:
    """
    Determine the local path where a file should be archived.

    Folder structure:
    - Photos/YYYY/YYYY-MM/filename
    - Videos/YYYY/YYYY-MM/filename
    - Documents/YYYY/YYYY-MM/filename
    - Audio/filename
    - Archives/filename
    - Installers/filename
    - Other/filename

    Args:
        archive_root: Root directory for the archive
        filename: Original file name
        mime_type: File MIME type (for classification)
        modified_date: File modification date (for year/month folders)

    Returns:
        Full path where the file should be saved
    """
    category = classify_file(filename, mime_type)

    if category in DATE_ORGANIZED_CATEGORIES and modified_date:
        year = str(modified_date.year)
        month = f"{modified_date.year}-{modified_date.month:02d}"
        return archive_root / category / year / month / filename
    else:
        return archive_root / category / filename


def parse_drive_date(date_str: str) -> Optional[datetime]:
    """
    Parse a date string from Google Drive API.

    Drive API returns dates in RFC 3339 format: 2024-01-15T10:30:00.000Z
    """
    if not date_str:
        return None

    try:
        # Remove the 'Z' suffix and parse
        if date_str.endswith("Z"):
            date_str = date_str[:-1]

        # Handle microseconds if present
        if "." in date_str:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f")
        else:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return None


def get_archive_structure_preview(archive_root: Path) -> str:
    """
    Get a text preview of the archive folder structure.

    Returns:
        Multi-line string showing folder structure
    """
    lines = [str(archive_root)]

    for category in ["Photos", "Videos", "Documents"]:
        lines.append(f"├── {category}/")
        lines.append(f"│   └── YYYY/")
        lines.append(f"│       └── YYYY-MM/")

    for category in ["Audio", "Archives", "Installers", "Other"]:
        lines.append(f"├── {category}/")

    return "\n".join(lines)
