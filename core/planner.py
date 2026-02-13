"""File eligibility rules and filtering."""

from typing import List, Dict, Any, Optional


class FileInfo:
    """Represents a Drive file with its metadata."""

    def __init__(self, data: Dict[str, Any]):
        self.id: str = data.get("id", "")
        self.name: str = data.get("name", "")
        self.size: int = int(data.get("size", 0))
        self.mime_type: str = data.get("mimeType", "")
        self.modified_time: str = data.get("modifiedTime", "")
        self.parents: List[str] = data.get("parents", [])
        self._raw = data

    @property
    def size_mb(self) -> float:
        """Size in megabytes."""
        return self.size / (1024 * 1024)

    def to_dict(self) -> Dict[str, Any]:
        """Convert back to dictionary."""
        return self._raw


# MIME types for Google Docs (these have size=0 in API but may export large)
GOOGLE_DOC_TYPES = {
    "application/vnd.google-apps.document",
    "application/vnd.google-apps.spreadsheet",
    "application/vnd.google-apps.presentation",
    "application/vnd.google-apps.drawing",
}

# MIME types to skip (shortcuts, forms, etc.)
SKIP_MIME_TYPES = {
    "application/vnd.google-apps.shortcut",
    "application/vnd.google-apps.form",
    "application/vnd.google-apps.map",
    "application/vnd.google-apps.site",
    "application/vnd.google-apps.folder",
}


def is_eligible_file(
    file_info: FileInfo,
    min_size_mb: int,
    before_date: str = "",
    include_google_docs: bool = True
) -> bool:
    """
    Check if a file is eligible for archiving.

    Eligibility criteria:
    - File size >= min_size_mb (for regular files)
    - File modified before before_date (if set)
    - Not a Google Docs type that can't be exported
    - Not a folder or shortcut

    Args:
        file_info: File metadata
        min_size_mb: Minimum size threshold in MB
        before_date: Only include files modified before this date (YYYY-MM-DD), empty to skip
        include_google_docs: Whether to include Google Docs files

    Returns:
        True if file is eligible for archiving
    """
    # Skip folders and special types
    if file_info.mime_type in SKIP_MIME_TYPES:
        return False

    # Check date filter (modifiedTime is ISO format from Drive API)
    if before_date and file_info.modified_time:
        if file_info.modified_time[:10] >= before_date:
            return False

    # Handle Google Docs types
    if file_info.mime_type in GOOGLE_DOC_TYPES:
        # Google Docs have size=0 in API, include if enabled
        return include_google_docs

    # Regular files: check size threshold
    return file_info.size_mb >= min_size_mb


def filter_eligible_files(
    files: List[Dict[str, Any]],
    min_size_mb: int,
    before_date: str = "",
    include_google_docs: bool = True
) -> List[FileInfo]:
    """
    Filter a list of files to only those eligible for archiving.

    Args:
        files: List of file metadata dictionaries from Drive API
        min_size_mb: Minimum size threshold in MB
        before_date: Only include files modified before this date (YYYY-MM-DD), empty to skip
        include_google_docs: Whether to include Google Docs files

    Returns:
        List of eligible FileInfo objects
    """
    eligible = []

    for file_data in files:
        file_info = FileInfo(file_data)
        if is_eligible_file(file_info, min_size_mb, before_date, include_google_docs):
            eligible.append(file_info)

    return eligible


def calculate_total_size(files: List[FileInfo]) -> int:
    """Calculate total size of files in bytes."""
    return sum(f.size for f in files)


def format_size(size_bytes: int) -> str:
    """Format size in bytes to human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
