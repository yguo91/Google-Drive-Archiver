"""Main window controller."""

from pathlib import Path
from typing import List, Dict, Any, Optional

from PySide6.QtCore import Slot, QThreadPool
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QMessageBox, QTableWidgetItem,
    QHeaderView, QVBoxLayout, QHBoxLayout, QGroupBox,
    QFormLayout, QLabel, QPushButton, QTableWidget, QStatusBar
)

from app import load_icon
from storage.config import Config
from core.planner import format_size
from core.classifier import classify_file
from core.organizer import parse_drive_date
from workers.scan_worker import ScanWorker
from workers.archive_worker import ArchiveWorker
from app.settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    """
    Main application window.

    Displays current settings, scan results, and archive controls.
    """

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self._files: List[Dict[str, Any]] = []
        self._scan_worker: Optional[ScanWorker] = None
        self._archive_worker: Optional[ArchiveWorker] = None
        self._thread_pool = QThreadPool()

        self._setup_ui()
        self._try_refresh_email()
        self._refresh_settings_display()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Build the main window UI."""
        self.setWindowTitle("Drive Archiver")
        self.setWindowIcon(load_icon("google drive icon.png"))
        self.resize(600, 523)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Settings group
        settings_group = QGroupBox("Current Settings")
        settings_layout = QFormLayout()

        self.lblAccountEmail = QLabel("---")
        settings_layout.addRow("Connected as:", self.lblAccountEmail)

        self.lblArchiveFolder = QLabel("---")
        settings_layout.addRow("Archive folder:", self.lblArchiveFolder)

        self.lblMinSize = QLabel("--- MB")
        settings_layout.addRow("Minimum Size:", self.lblMinSize)

        self.lblDryRun = QLabel("On / Off")
        settings_layout.addRow("Dry run:", self.lblDryRun)

        self.lblTrashAfter = QLabel("On / Off")
        settings_layout.addRow("Trash after download:", self.lblTrashAfter)

        # Buttons row
        buttons_layout = QHBoxLayout()
        self.btnOpenSettings = QPushButton("Settings...")
        buttons_layout.addWidget(self.btnOpenSettings)

        self.btnScan = QPushButton("Scan Google Drive")
        buttons_layout.addWidget(self.btnScan)

        settings_layout.addRow(buttons_layout)
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)

        # Scan summary group
        summary_group = QGroupBox("Scan Summary")
        summary_layout = QVBoxLayout()

        self.lblFilesFound = QLabel("Files found: 0")
        summary_layout.addWidget(self.lblFilesFound)

        self.lblSpaceToFree = QLabel("Estimated space to free: 0 MB")
        summary_layout.addWidget(self.lblSpaceToFree)

        # Files table
        self.tblFiles = QTableWidget()
        self.tblFiles.setColumnCount(4)
        self.tblFiles.setHorizontalHeaderLabels(["File Name", "Size", "Type", "Date"])
        self.tblFiles.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tblFiles.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tblFiles.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)

        header = self.tblFiles.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        summary_layout.addWidget(self.tblFiles)
        summary_group.setLayout(summary_layout)
        main_layout.addWidget(summary_group)

        # Archive buttons
        archive_layout = QHBoxLayout()
        self.btnArchiveAll = QPushButton("Archive All")
        archive_layout.addWidget(self.btnArchiveAll)

        self.btnArchiveSelected = QPushButton("Archive Selected")
        archive_layout.addWidget(self.btnArchiveSelected)

        main_layout.addLayout(archive_layout)

        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

    def _connect_signals(self) -> None:
        """Connect UI signals to handlers."""
        self.btnOpenSettings.clicked.connect(self._on_settings_clicked)
        self.btnScan.clicked.connect(self._on_scan_clicked)
        self.btnArchiveAll.clicked.connect(self._on_archive_all_clicked)
        self.btnArchiveSelected.clicked.connect(self._on_archive_selected_clicked)

    def _try_refresh_email(self) -> None:
        """Refresh account email from Google if it's missing or unknown."""
        email = self.config.account_email
        if email and email not in ("", "Unknown"):
            return
        try:
            from infra.auth import get_credentials, get_user_email
            creds = get_credentials()
            if creds:
                fetched = get_user_email(creds)
                if fetched and fetched != "Unknown":
                    self.config.account_email = fetched
                    self.config.save()
        except Exception:
            pass

    def _refresh_settings_display(self) -> None:
        """Update the settings display with current config values."""
        self.lblAccountEmail.setText(self.config.account_email or "Not connected")
        self.lblArchiveFolder.setText(self.config.archive_path or "Not set")
        self.lblMinSize.setText(f"{self.config.min_size_mb} MB")
        self.lblDryRun.setText("On" if self.config.dry_run else "Off")
        self.lblTrashAfter.setText("On" if self.config.trash_after else "Off")

    @Slot()
    def _on_settings_clicked(self) -> None:
        """Open settings dialog."""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            # Refresh display after settings change
            self._refresh_settings_display()

    @Slot()
    def _on_scan_clicked(self) -> None:
        """Start scanning Google Drive."""
        if self._scan_worker is not None:
            return  # Already scanning

        self._files = []
        self._clear_table()
        self._update_status("Scanning...")
        self._set_buttons_enabled(False)

        self._scan_worker = ScanWorker(self.config.min_size_mb)
        self._scan_worker.signals.progress.connect(self._on_scan_progress)
        self._scan_worker.signals.finished.connect(self._on_scan_finished)
        self._scan_worker.signals.error.connect(self._on_scan_error)
        self._scan_worker.signals.status.connect(self._update_status)

        self._thread_pool.start(self._scan_worker)

    @Slot(int)
    def _on_scan_progress(self, count: int) -> None:
        """Handle scan progress update."""
        self._update_status(f"Scanning... found {count} files")

    @Slot(list)
    def _on_scan_finished(self, files: List[Dict[str, Any]]) -> None:
        """Handle scan completion."""
        self._scan_worker = None
        self._files = files
        self._populate_table(files)
        self._set_buttons_enabled(True)

        # Update summary
        total_size = sum(int(f.get("size", 0)) for f in files)
        self.lblFilesFound.setText(f"Files found: {len(files)}")
        self.lblSpaceToFree.setText(f"Estimated space to free: {format_size(total_size)}")

        self._update_status(f"Scan complete - {len(files)} files found")

    @Slot(str)
    def _on_scan_error(self, error: str) -> None:
        """Handle scan error."""
        self._scan_worker = None
        self._set_buttons_enabled(True)
        self._update_status("Scan failed")

        QMessageBox.critical(self, "Scan Error", error)

    def _populate_table(self, files: List[Dict[str, Any]]) -> None:
        """Populate the files table with scan results."""
        self.tblFiles.setRowCount(len(files))

        for row, file_data in enumerate(files):
            # File name
            name = file_data.get("name", "")
            self.tblFiles.setItem(row, 0, QTableWidgetItem(name))

            # Size
            size = int(file_data.get("size", 0))
            self.tblFiles.setItem(row, 1, QTableWidgetItem(format_size(size)))

            # Type (category)
            mime_type = file_data.get("mimeType", "")
            category = classify_file(name, mime_type)
            self.tblFiles.setItem(row, 2, QTableWidgetItem(category))

            # Date
            date_str = file_data.get("modifiedTime", "")
            date = parse_drive_date(date_str)
            if date:
                formatted_date = date.strftime("%Y-%m-%d")
            else:
                formatted_date = ""
            self.tblFiles.setItem(row, 3, QTableWidgetItem(formatted_date))

    def _clear_table(self) -> None:
        """Clear the files table."""
        self.tblFiles.setRowCount(0)
        self.lblFilesFound.setText("Files found: 0")
        self.lblSpaceToFree.setText("Estimated space to free: 0 MB")

    @Slot()
    def _on_archive_all_clicked(self) -> None:
        """Archive all files in the table."""
        if not self._files:
            QMessageBox.information(self, "No Files", "No files to archive. Run a scan first.")
            return

        self._start_archive(self._files)

    @Slot()
    def _on_archive_selected_clicked(self) -> None:
        """Archive selected files only."""
        selected_rows = set(index.row() for index in self.tblFiles.selectedIndexes())

        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select files to archive.")
            return

        selected_files = [self._files[row] for row in sorted(selected_rows)]
        self._start_archive(selected_files)

    def _start_archive(self, files: List[Dict[str, Any]]) -> None:
        """Start the archive operation."""
        if self._archive_worker is not None:
            return  # Already archiving

        # Confirm with user
        mode = "simulate archiving" if self.config.dry_run else "archive"
        action = f"{mode} {len(files)} files"
        if self.config.trash_after and not self.config.dry_run:
            action += " (originals will be trashed)"

        reply = QMessageBox.question(
            self,
            "Confirm Archive",
            f"Are you sure you want to {action}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        self._set_buttons_enabled(False)
        self._update_status("Archiving...")

        self._archive_worker = ArchiveWorker(
            files=files,
            archive_path=self.config.archive_path,
            dry_run=self.config.dry_run,
            trash_after=self.config.trash_after
        )
        self._archive_worker.signals.progress.connect(self._on_archive_progress)
        self._archive_worker.signals.finished.connect(self._on_archive_finished)
        self._archive_worker.signals.error.connect(self._on_archive_error)
        self._archive_worker.signals.status.connect(self._update_status)

        self._thread_pool.start(self._archive_worker)

    @Slot(int, int, str)
    def _on_archive_progress(self, current: int, total: int, filename: str) -> None:
        """Handle archive progress update."""
        self._update_status(f"Archiving {current}/{total}: {filename}")

    @Slot(int, int)
    def _on_archive_finished(self, success: int, failed: int) -> None:
        """Handle archive completion."""
        self._archive_worker = None
        self._set_buttons_enabled(True)

        mode = "Dry run" if self.config.dry_run else "Archive"
        message = f"{mode} complete: {success} succeeded"
        if failed > 0:
            message += f", {failed} failed"

        self._update_status(message)

        QMessageBox.information(self, "Archive Complete", message)

    @Slot(str)
    def _on_archive_error(self, error: str) -> None:
        """Handle archive error."""
        self._archive_worker = None
        self._set_buttons_enabled(True)
        self._update_status("Archive failed")

        QMessageBox.critical(self, "Archive Error", error)

    def _set_buttons_enabled(self, enabled: bool) -> None:
        """Enable or disable action buttons."""
        self.btnScan.setEnabled(enabled)
        self.btnArchiveAll.setEnabled(enabled)
        self.btnArchiveSelected.setEnabled(enabled)

    def _update_status(self, message: str) -> None:
        """Update the status bar message."""
        self.statusBar.showMessage(message)

    def closeEvent(self, event) -> None:
        """Handle window close - cancel any running workers."""
        if self._scan_worker:
            self._scan_worker.cancel()
        if self._archive_worker:
            self._archive_worker.cancel()

        self._thread_pool.waitForDone(3000)
        event.accept()
