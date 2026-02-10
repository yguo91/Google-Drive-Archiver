"""Settings dialog controller."""

from pathlib import Path

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QDialog, QFileDialog, QMessageBox, QVBoxLayout, QGroupBox,
    QFormLayout, QLineEdit, QPushButton, QSpinBox, QCheckBox,
    QLabel, QDialogButtonBox
)

from app import load_icon
from storage.config import Config


class SettingsDialog(QDialog):
    """
    Settings dialog for modifying application configuration.

    Allows changing:
    - Archive folder path
    - Minimum file size threshold
    - Dry run mode
    - Trash after download option
    """

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config

        self._setup_ui()
        self._load_current_settings()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Build the dialog UI programmatically."""
        self.setWindowTitle("Settings")
        self.setWindowIcon(load_icon("google drive icon.png"))
        self.setMinimumSize(520, 280)
        self.setModal(True)

        main_layout = QVBoxLayout()

        # Storage group
        storage_group = QGroupBox("Storage")
        storage_layout = QFormLayout()

        self.txtArchivePath = QLineEdit()
        self.txtArchivePath.setReadOnly(True)
        self.txtArchivePath.setPlaceholderText("Choose a folder...")
        storage_layout.addRow("Archive folder:", self.txtArchivePath)

        self.btnBrowseArchive = QPushButton("Browse...")
        storage_layout.addRow("", self.btnBrowseArchive)

        storage_group.setLayout(storage_layout)
        main_layout.addWidget(storage_group)

        # Rules group
        rules_group = QGroupBox("Rules")
        rules_layout = QFormLayout()

        self.spinMinSizeMb = QSpinBox()
        self.spinMinSizeMb.setMinimum(10)
        self.spinMinSizeMb.setMaximum(102400)
        self.spinMinSizeMb.setValue(200)
        self.spinMinSizeMb.setSuffix(" MB")
        rules_layout.addRow("Minimum file size:", self.spinMinSizeMb)

        self.chkDryRun = QCheckBox("Dry run (do not change anything)")
        self.chkDryRun.setChecked(True)
        dry_run_note = QLabel("* When enabled, the app will only show what would happen.")
        dry_run_note.setWordWrap(True)
        rules_layout.addRow(self.chkDryRun, dry_run_note)

        self.chkTrashAfter = QCheckBox("Move originals to Trash after download")
        self.chkTrashAfter.setChecked(True)
        trash_note = QLabel("* You can restore items from Trash later.")
        rules_layout.addRow(self.chkTrashAfter, trash_note)

        rules_group.setLayout(rules_layout)
        main_layout.addWidget(rules_group)

        # Button box
        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        main_layout.addWidget(self.buttonBox)

        self.setLayout(main_layout)

    def _load_current_settings(self) -> None:
        """Load current config values into widgets."""
        self.txtArchivePath.setText(self.config.archive_path)
        self.spinMinSizeMb.setValue(self.config.min_size_mb)
        self.chkDryRun.setChecked(self.config.dry_run)
        self.chkTrashAfter.setChecked(self.config.trash_after)

    def _connect_signals(self) -> None:
        """Connect UI signals to handlers."""
        self.btnBrowseArchive.clicked.connect(self._on_browse_clicked)
        self.buttonBox.accepted.connect(self._on_accepted)
        self.buttonBox.rejected.connect(self.reject)

    @Slot()
    def _on_browse_clicked(self) -> None:
        """Handle Browse button click."""
        current_path = self.txtArchivePath.text()

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Archive Folder",
            current_path,
        )

        if folder:
            self.txtArchivePath.setText(folder)

    @Slot()
    def _on_accepted(self) -> None:
        """Handle OK button - validate and save settings."""
        # Validate archive path
        archive_path = self.txtArchivePath.text()

        if not archive_path:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please select an archive folder."
            )
            return

        # Check if path is valid
        path = Path(archive_path)
        if not path.parent.exists():
            QMessageBox.warning(
                self,
                "Validation Error",
                f"The parent directory does not exist:\n{path.parent}"
            )
            return

        # Save settings
        self.config.archive_path = archive_path
        self.config.min_size_mb = self.spinMinSizeMb.value()
        self.config.dry_run = self.chkDryRun.isChecked()
        self.config.trash_after = self.chkTrashAfter.isChecked()

        self.config.save()

        self.accept()
