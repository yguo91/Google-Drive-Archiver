"""Google Drive API client wrapper."""

import io
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

from infra.auth import get_credentials, CredentialsMissingError


# Google Docs export MIME types
GOOGLE_DOC_EXPORTS = {
    "application/vnd.google-apps.document": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".docx"
    ),
    "application/vnd.google-apps.spreadsheet": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xlsx"
    ),
    "application/vnd.google-apps.presentation": (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".pptx"
    ),
    "application/vnd.google-apps.drawing": (
        "image/png",
        ".png"
    ),
}

# Google Docs types that need export (not direct download)
GOOGLE_DOC_TYPES = set(GOOGLE_DOC_EXPORTS.keys())


class DriveClientError(Exception):
    """Drive client error."""
    pass


class DriveClient:
    """Google Drive API client for listing, downloading, and managing files."""

    def __init__(self, credentials: Optional[Credentials] = None):
        """
        Initialize the Drive client.

        Args:
            credentials: OAuth credentials. If None, loads from saved token.
        """
        if credentials is None:
            credentials = get_credentials()

        if credentials is None:
            raise CredentialsMissingError()

        self._service = build("drive", "v3", credentials=credentials)

    def list_files(
        self,
        min_size_mb: int = 0,
        page_size: int = 100,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        List files in Drive that meet the size threshold.

        The Drive API v3 does not support filtering by 'size' in the query
        parameter, so we fetch all non-trashed files owned by the user and
        filter by size client-side.

        Args:
            min_size_mb: Minimum file size in MB
            page_size: Number of results per API call
            progress_callback: Called with count of files found so far

        Returns:
            List of file metadata dictionaries
        """
        min_size_bytes = min_size_mb * 1024 * 1024

        # Drive API v3 query: 'size' is NOT a valid query term,
        # so we filter client-side after fetching.
        query = "'me' in owners and trashed = false"

        files = []
        page_token = None

        while True:
            try:
                results = self._service.files().list(
                    q=query,
                    pageSize=page_size,
                    pageToken=page_token,
                    fields="nextPageToken, files(id, name, size, mimeType, modifiedTime, parents)",
                    orderBy="modifiedTime desc"
                ).execute()

                batch = results.get("files", [])

                # Filter by size client-side
                for f in batch:
                    file_size = int(f.get("size", 0))
                    if file_size >= min_size_bytes:
                        files.append(f)

                if progress_callback:
                    progress_callback(len(files))

                page_token = results.get("nextPageToken")
                if not page_token:
                    break

            except HttpError as e:
                raise DriveClientError(f"Failed to list files: {e}")

        return files

    def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """Get metadata for a specific file."""
        try:
            return self._service.files().get(
                fileId=file_id,
                fields="id, name, size, mimeType, modifiedTime, parents"
            ).execute()
        except HttpError as e:
            raise DriveClientError(f"Failed to get file info: {e}")

    def download_file(
        self,
        file_id: str,
        dest_path: Path,
        mime_type: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Path:
        """
        Download a file from Drive.

        Args:
            file_id: The file's Drive ID
            dest_path: Destination path for the downloaded file
            mime_type: The file's MIME type (to determine if export needed)
            progress_callback: Called with (bytes_downloaded, total_bytes)

        Returns:
            The actual path where file was saved (may differ for Google Docs)
        """
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if this is a Google Doc that needs export
        if mime_type in GOOGLE_DOC_TYPES:
            return self._export_google_doc(file_id, dest_path, mime_type, progress_callback)

        return self._download_binary_file(file_id, dest_path, progress_callback)

    def _download_binary_file(
        self,
        file_id: str,
        dest_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Path:
        """Download a regular (non-Google Docs) file."""
        try:
            request = self._service.files().get_media(fileId=file_id)

            with open(dest_path, "wb") as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False

                while not done:
                    status, done = downloader.next_chunk()
                    if progress_callback and status:
                        progress_callback(
                            int(status.resumable_progress),
                            int(status.total_size)
                        )

            return dest_path

        except HttpError as e:
            raise DriveClientError(f"Failed to download file: {e}")

    def _export_google_doc(
        self,
        file_id: str,
        dest_path: Path,
        mime_type: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Path:
        """Export a Google Docs/Sheets/Slides file."""
        export_mime, extension = GOOGLE_DOC_EXPORTS[mime_type]

        # Update destination path with correct extension
        actual_path = dest_path.with_suffix(extension)

        try:
            request = self._service.files().export_media(
                fileId=file_id,
                mimeType=export_mime
            )

            with open(actual_path, "wb") as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False

                while not done:
                    status, done = downloader.next_chunk()
                    if progress_callback and status:
                        progress_callback(
                            int(status.resumable_progress or 0),
                            int(status.total_size or 0)
                        )

            return actual_path

        except HttpError as e:
            raise DriveClientError(f"Failed to export file: {e}")

    def trash_file(self, file_id: str) -> None:
        """Move a file to Trash."""
        try:
            self._service.files().update(
                fileId=file_id,
                body={"trashed": True}
            ).execute()
        except HttpError as e:
            raise DriveClientError(f"Failed to trash file: {e}")

    def get_file_path(self, file_id: str) -> str:
        """Get the full path of a file in Drive (folder structure)."""
        try:
            path_parts = []
            current_id = file_id

            while current_id:
                file_info = self._service.files().get(
                    fileId=current_id,
                    fields="name, parents"
                ).execute()

                path_parts.insert(0, file_info.get("name", ""))
                parents = file_info.get("parents", [])

                if parents:
                    current_id = parents[0]
                else:
                    break

            return "/".join(path_parts)

        except HttpError:
            return ""

    def is_google_doc(self, mime_type: str) -> bool:
        """Check if a MIME type is a Google Docs type."""
        return mime_type in GOOGLE_DOC_TYPES


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
