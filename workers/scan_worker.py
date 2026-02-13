"""Background worker for scanning Google Drive files."""

from typing import List

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from infra.drive_client import DriveClient, DriveClientError
from core.planner import FileInfo, filter_eligible_files


class ScanWorkerSignals(QObject):
    """Signals for the scan worker."""

    # Emitted with count of files found so far
    progress = Signal(int)

    # Emitted when scan completes successfully with list of eligible files
    finished = Signal(list)

    # Emitted on error with error message
    error = Signal(str)

    # Emitted with status message
    status = Signal(str)


class ScanWorker(QRunnable):
    """
    Background worker for scanning Google Drive.

    Scans Drive for files meeting the size threshold and emits
    progress updates during the scan.
    """

    def __init__(self, min_size_mb: int, before_date: str = ""):
        """
        Initialize the scan worker.

        Args:
            min_size_mb: Minimum file size in MB to include
            before_date: Only include files modified before this date (YYYY-MM-DD), empty to skip
        """
        super().__init__()
        self.min_size_mb = min_size_mb
        self.before_date = before_date
        self.signals = ScanWorkerSignals()
        self._cancelled = False

    def cancel(self) -> None:
        """Request cancellation of the scan."""
        self._cancelled = True

    @Slot()
    def run(self) -> None:
        """Execute the scan operation."""
        try:
            self.signals.status.emit("Connecting to Google Drive...")

            client = DriveClient()

            self.signals.status.emit("Scanning files...")

            # Fetch files with progress updates
            files = client.list_files(
                min_size_mb=self.min_size_mb,
                before_date=self.before_date,
                progress_callback=self._on_progress
            )

            if self._cancelled:
                self.signals.status.emit("Scan cancelled")
                return

            self.signals.status.emit("Filtering eligible files...")

            # Filter to eligible files
            eligible = filter_eligible_files(
                files,
                min_size_mb=self.min_size_mb,
                before_date=self.before_date,
                include_google_docs=True
            )

            # Convert to serializable format for signal
            result = [f.to_dict() for f in eligible]

            self.signals.status.emit(f"Found {len(result)} files")
            self.signals.finished.emit(result)

        except DriveClientError as e:
            self.signals.error.emit(str(e))
        except Exception as e:
            self.signals.error.emit(f"Scan failed: {e}")

    def _on_progress(self, count: int) -> None:
        """Handle progress update from API."""
        if not self._cancelled:
            self.signals.progress.emit(count)
