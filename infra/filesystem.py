"""Safe file system operations."""

import hashlib
import os
import shutil
from pathlib import Path
from typing import Optional, Tuple


class FileSystemError(Exception):
    """File system operation error."""
    pass


def get_disk_free_space(path: Path) -> int:
    """
    Get free disk space for the drive containing the given path.

    Args:
        path: Any path on the target drive

    Returns:
        Free space in bytes
    """
    try:
        # Get the root/drive of the path
        if path.exists():
            target = path
        else:
            # Find nearest existing parent
            target = path
            while not target.exists() and target.parent != target:
                target = target.parent

        usage = shutil.disk_usage(target)
        return usage.free
    except OSError as e:
        raise FileSystemError(f"Could not get disk space: {e}")


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


def ensure_dir(path: Path) -> None:
    """Create directory and parents if they don't exist."""
    path.mkdir(parents=True, exist_ok=True)


def safe_write(dest_path: Path, data: bytes) -> None:
    """
    Safely write data to a file using atomic write pattern.

    Writes to a temp file first, then renames to avoid partial writes.
    """
    ensure_dir(dest_path.parent)

    temp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")

    try:
        with open(temp_path, "wb") as f:
            f.write(data)

        # Atomic rename
        temp_path.replace(dest_path)
    except OSError as e:
        # Clean up temp file if it exists
        if temp_path.exists():
            temp_path.unlink()
        raise FileSystemError(f"Failed to write file: {e}")


def calculate_md5(file_path: Path, chunk_size: int = 8192) -> str:
    """Calculate MD5 hash of a file."""
    md5 = hashlib.md5()

    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            md5.update(chunk)

    return md5.hexdigest()


def verify_download(local_path: Path, expected_size: Optional[int] = None) -> bool:
    """
    Verify a downloaded file.

    Args:
        local_path: Path to the downloaded file
        expected_size: Expected file size in bytes (if known)

    Returns:
        True if file appears valid
    """
    if not local_path.exists():
        return False

    actual_size = local_path.stat().st_size

    # File must not be empty
    if actual_size == 0:
        return False

    # Check size if expected size is provided
    if expected_size is not None and actual_size != expected_size:
        return False

    return True


def get_unique_path(dest_path: Path) -> Path:
    """
    Get a unique file path by appending a number if file exists.

    Example: file.txt -> file (1).txt -> file (2).txt
    """
    if not dest_path.exists():
        return dest_path

    stem = dest_path.stem
    suffix = dest_path.suffix
    parent = dest_path.parent

    counter = 1
    while True:
        new_path = parent / f"{stem} ({counter}){suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


def clean_filename(filename: str) -> str:
    """
    Clean a filename to be safe for the file system.

    Removes or replaces invalid characters.
    """
    # Characters not allowed in Windows filenames
    invalid_chars = '<>:"/\\|?*'

    cleaned = filename
    for char in invalid_chars:
        cleaned = cleaned.replace(char, "_")

    # Remove leading/trailing spaces and dots
    cleaned = cleaned.strip(" .")

    # Ensure non-empty
    if not cleaned:
        cleaned = "unnamed"

    return cleaned


def delete_file(file_path: Path) -> None:
    """Delete a file if it exists."""
    if file_path.exists():
        file_path.unlink()
