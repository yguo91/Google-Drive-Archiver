"""Background worker for archiving files from Google Drive."""

from pathlib import Path
from typing import List, Dict, Any

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from infra.drive_client import DriveClient, DriveClientError
from infra.filesystem import verify_download, get_unique_path, clean_filename
from core.organizer import get_local_path, parse_drive_date
from core.planner import FileInfo


class ArchiveWorkerSignals(QObject):
    """Signals for the archive worker."""

    # Emitted with (current_index, total_count, filename)
    progress = Signal(int, int, str)

    # Emitted with (bytes_downloaded, total_bytes) for current file
    file_progress = Signal(int, int)

    # Emitted when archive completes with (success_count, fail_count)
    finished = Signal(int, int)

    # Emitted on error with error message
    error = Signal(str)

    # Emitted with status message
    status = Signal(str)

    # Emitted for each file result: (filename, success, message)
    file_result = Signal(str, bool, str)


class ArchiveWorker(QRunnable):
    """
    Background worker for downloading and archiving files.

    Downloads files to the local archive, verifies downloads,
    and optionally moves originals to Trash.
    """

    def __init__(
        self,
        files: List[Dict[str, Any]],
        archive_path: str,
        dry_run: bool = True,
        trash_after: bool = True
    ):
        """
        Initialize the archive worker.

        Args:
            files: List of file metadata dictionaries to archive
            archive_path: Local archive root directory
            dry_run: If True, only simulate actions
            trash_after: If True, move originals to Trash after download
        """
        super().__init__()
        self.files = [FileInfo(f) for f in files]
        self.archive_path = Path(archive_path)
        self.dry_run = dry_run
        self.trash_after = trash_after
        self.signals = ArchiveWorkerSignals()
        self._cancelled = False

    def cancel(self) -> None:
        """Request cancellation of the archive operation."""
        self._cancelled = True

    @Slot()
    def run(self) -> None:
        """Execute the archive operation."""
        success_count = 0
        fail_count = 0
        total = len(self.files)

        try:
            if not self.dry_run:
                self.signals.status.emit("Connecting to Google Drive...")
                client = DriveClient()
            else:
                client = None
                self.signals.status.emit("Dry run - simulating archive...")

            for i, file_info in enumerate(self.files):
                if self._cancelled:
                    self.signals.status.emit("Archive cancelled")
                    break

                self.signals.progress.emit(i + 1, total, file_info.name)

                try:
                    success = self._process_file(client, file_info)
                    if success:
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    fail_count += 1
                    self.signals.file_result.emit(
                        file_info.name,
                        False,
                        f"Error: {e}"
                    )

            mode = "Dry run" if self.dry_run else "Archive"
            self.signals.status.emit(
                f"{mode} complete: {success_count} succeeded, {fail_count} failed"
            )
            self.signals.finished.emit(success_count, fail_count)

        except DriveClientError as e:
            self.signals.error.emit(str(e))
        except Exception as e:
            self.signals.error.emit(f"Archive failed: {e}")

    def _process_file(self, client: DriveClient, file_info: FileInfo) -> bool:
        """
        Process a single file.

        Returns:
            True if successful
        """
        # Determine local path
        modified_date = parse_drive_date(file_info.modified_time)
        clean_name = clean_filename(file_info.name)

        local_path = get_local_path(
            archive_root=self.archive_path,
            filename=clean_name,
            mime_type=file_info.mime_type,
            modified_date=modified_date
        )

        # Get unique path if file exists
        local_path = get_unique_path(local_path)

        if self.dry_run:
            # Simulate the operation
            action = "Would download"
            if self.trash_after:
                action += " and trash"

            self.signals.file_result.emit(
                file_info.name,
                True,
                f"{action} to {local_path}"
            )
            return True

        # Download the file
        self.signals.status.emit(f"Downloading: {file_info.name}")

        try:
            actual_path = client.download_file(
                file_id=file_info.id,
                dest_path=local_path,
                mime_type=file_info.mime_type,
                progress_callback=self._on_file_progress
            )

            # Verify download (skip size check for Google Docs as they export differently)
            is_google_doc = client.is_google_doc(file_info.mime_type)
            expected_size = None if is_google_doc else file_info.size

            if not verify_download(actual_path, expected_size):
                self.signals.file_result.emit(
                    file_info.name,
                    False,
                    "Download verification failed"
                )
                return False

            # Trash the original if enabled
            if self.trash_after:
                self.signals.status.emit(f"Moving to trash: {file_info.name}")
                client.trash_file(file_info.id)

            action = "Downloaded"
            if self.trash_after:
                action += " and trashed"

            self.signals.file_result.emit(
                file_info.name,
                True,
                f"{action} to {actual_path}"
            )
            return True

        except DriveClientError as e:
            self.signals.file_result.emit(
                file_info.name,
                False,
                str(e)
            )
            return False

    def _on_file_progress(self, downloaded: int, total: int) -> None:
        """Handle download progress for current file."""
        self.signals.file_progress.emit(downloaded, total)
