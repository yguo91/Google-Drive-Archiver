"""Onboarding wizard controller."""

from pathlib import Path

from PySide6.QtCore import Slot, QFile, QIODevice
from PySide6.QtWidgets import QWizard, QWizardPage, QFileDialog, QMessageBox
from PySide6.QtUiTools import QUiLoader

from app import load_icon
from storage.config import Config
from infra.auth import authenticate, CredentialsMissingError, AuthError
from infra.filesystem import get_disk_free_space, format_size


class OnboardingWizard(QWizard):
    """
    Setup wizard for first-time configuration.

    Pages:
    1. Welcome - explanation and consent checkbox
    2. Connect - Google Drive OAuth
    3. Archive Folder - select local folder
    4. Rules - size threshold and options
    """

    PAGE_WELCOME = 0
    PAGE_CONNECT = 1
    PAGE_ARCHIVE = 2
    PAGE_RULES = 3

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self._connected = False
        self._account_email = ""
        self._archive_path = ""

        self.setWindowIcon(load_icon("google drive icon.png"))
        self._load_ui()
        self._connect_signals()

    def _load_ui(self) -> None:
        """Load the wizard from UI file and extract pages."""
        loader = QUiLoader()
        ui_path = Path(__file__).parent.parent / "wizard_onboarding.ui"

        ui_file = QFile(str(ui_path))
        if not ui_file.open(QIODevice.OpenModeFlag.ReadOnly):
            raise RuntimeError(f"Cannot open UI file: {ui_path}")

        loaded_wizard = loader.load(ui_file, None)
        ui_file.close()

        if not loaded_wizard:
            raise RuntimeError("Failed to load wizard UI")

        # Set up this wizard with properties from loaded
        self.setWindowTitle(loaded_wizard.windowTitle())
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)

        # Create pages manually since we can't directly transfer QWizardPages
        self._create_pages(loaded_wizard)

    def _create_pages(self, loaded: QWizard) -> None:
        """Create wizard pages based on the loaded UI."""
        # Page 0: Welcome
        page_welcome = QWizardPage()
        page_welcome.setTitle("Welcome")
        page_welcome.setSubTitle("Google Drive Archive & Cleanup Tool")

        # Find widgets from loaded wizard
        loaded_page = loaded.page(0)
        if loaded_page:
            self.chkUnderstandTrash = loaded_page.findChild(loaded_page.__class__.mro()[1], "chkUnderstandTrash")

        from PySide6.QtWidgets import QVBoxLayout, QLabel, QCheckBox

        layout = QVBoxLayout()
        label = QLabel(
            "<p style='font-size: 11pt;'>This tool scans Google Drive for large files.</p>"
            "<p style='font-size: 11pt;'>Downloads them to your PC in an organized archive.</p>"
            "<p style='font-size: 11pt;'>Moves originals to Trash after download.</p>"
        )
        label.setWordWrap(True)
        layout.addWidget(label)

        self.chkUnderstandTrash = QCheckBox("I understand files will be moved to Trash")
        layout.addWidget(self.chkUnderstandTrash)
        layout.addStretch()

        page_welcome.setLayout(layout)
        self.addPage(page_welcome)

        # Page 1: Connect
        page_connect = QWizardPage()
        page_connect.setTitle("Connect")
        page_connect.setSubTitle("Connect your Google Drive account")

        from PySide6.QtWidgets import QGroupBox, QPushButton

        layout = QVBoxLayout()
        group = QGroupBox("Google Drive Account")
        group_layout = QVBoxLayout()

        self.btnConnectDrive = QPushButton("Connect Google Drive")
        group_layout.addWidget(self.btnConnectDrive)

        self.lblConnectStatus = QLabel("You must connect before continuing")
        group_layout.addWidget(self.lblConnectStatus)

        group.setLayout(group_layout)
        layout.addWidget(group)
        layout.addStretch()

        page_connect.setLayout(layout)
        self.addPage(page_connect)

        # Page 2: Archive Folder
        page_archive = QWizardPage()
        page_archive.setTitle("Archive Folder")
        page_archive.setSubTitle("Choose where to save archived files")

        from PySide6.QtWidgets import QLineEdit

        layout = QVBoxLayout()

        self.txtArchiveFolder = QLineEdit()
        self.txtArchiveFolder.setReadOnly(True)
        self.txtArchiveFolder.setPlaceholderText("Select a folder...")
        layout.addWidget(self.txtArchiveFolder)

        self.btnBrowseArchive = QPushButton("Browse...")
        layout.addWidget(self.btnBrowseArchive)

        self.lblDiskFree = QLabel("Free space: --")
        layout.addWidget(self.lblDiskFree)
        layout.addStretch()

        page_archive.setLayout(layout)
        self.addPage(page_archive)

        # Page 3: Rules
        page_rules = QWizardPage()
        page_rules.setTitle("Rules")
        page_rules.setSubTitle("Configure archive rules")

        from PySide6.QtCore import QDate
        from PySide6.QtWidgets import QSpinBox, QHBoxLayout, QDateEdit, QRadioButton

        layout = QVBoxLayout()

        # Filter mode radio buttons
        self.radioFilterBySize = QRadioButton("Filter by file size")
        self.radioFilterBySize.setChecked(True)
        layout.addWidget(self.radioFilterBySize)

        size_layout = QHBoxLayout()
        size_label = QLabel("  Minimum file size:")
        size_layout.addWidget(size_label)

        self.spinMinSize = QSpinBox()
        self.spinMinSize.setMinimum(10)
        self.spinMinSize.setMaximum(102400)
        self.spinMinSize.setValue(200)
        self.spinMinSize.setSuffix(" MB")
        size_layout.addWidget(self.spinMinSize)
        layout.addLayout(size_layout)

        self.radioFilterByDate = QRadioButton("Filter by date")
        layout.addWidget(self.radioFilterByDate)

        date_layout = QHBoxLayout()
        date_label = QLabel("  Modified before:")
        date_layout.addWidget(date_label)
        self.dateBeforeDate = QDateEdit()
        self.dateBeforeDate.setCalendarPopup(True)
        self.dateBeforeDate.setDisplayFormat("yyyy-MM-dd")
        self.dateBeforeDate.setDate(QDate(2020, 1, 1))
        self.dateBeforeDate.setEnabled(False)
        date_layout.addWidget(self.dateBeforeDate)
        layout.addLayout(date_layout)

        def _on_filter_mode_changed():
            by_size = self.radioFilterBySize.isChecked()
            self.spinMinSize.setEnabled(by_size)
            self.dateBeforeDate.setEnabled(not by_size)

        self.radioFilterBySize.toggled.connect(_on_filter_mode_changed)

        self.chkDryRun = QCheckBox("Dry run first (recommended)")
        self.chkDryRun.setChecked(True)
        layout.addWidget(self.chkDryRun)

        self.chkTrashAfter = QCheckBox("Move originals to Trash after download")
        self.chkTrashAfter.setChecked(True)
        layout.addWidget(self.chkTrashAfter)
        layout.addStretch()

        page_rules.setLayout(layout)
        self.addPage(page_rules)

    def _connect_signals(self) -> None:
        """Connect UI signals to handlers."""
        self.btnConnectDrive.clicked.connect(self._on_connect_clicked)
        self.btnBrowseArchive.clicked.connect(self._on_browse_clicked)

    @Slot()
    def _on_connect_clicked(self) -> None:
        """Handle Connect button click."""
        try:
            creds, email = authenticate()
            self._connected = True
            self._account_email = email

            self.lblConnectStatus.setText(f"Connected as: {email}")
            self.btnConnectDrive.setText("Connected")
            self.btnConnectDrive.setEnabled(False)

        except CredentialsMissingError as e:
            QMessageBox.critical(
                self,
                "Credentials Missing",
                str(e)
            )
        except AuthError as e:
            QMessageBox.warning(
                self,
                "Connection Failed",
                str(e)
            )

    @Slot()
    def _on_browse_clicked(self) -> None:
        """Handle Browse button click."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Archive Folder",
            "",
        )

        if folder:
            self._archive_path = folder
            self.txtArchiveFolder.setText(folder)

            # Update disk space display
            try:
                free_space = get_disk_free_space(Path(folder))
                self.lblDiskFree.setText(f"Free space: {format_size(free_space)}")
            except Exception:
                self.lblDiskFree.setText("Free space: Unknown")

    def validateCurrentPage(self) -> bool:
        """Validate the current page before proceeding."""
        current_id = self.currentId()

        # Welcome page: must check the consent checkbox
        if current_id == self.PAGE_WELCOME:
            if not self.chkUnderstandTrash.isChecked():
                QMessageBox.warning(
                    self,
                    "Consent Required",
                    "Please check the box to confirm you understand files will be moved to Trash."
                )
                return False

        # Connect page: must be connected
        elif current_id == self.PAGE_CONNECT:
            if not self._connected:
                QMessageBox.warning(
                    self,
                    "Connection Required",
                    "Please connect your Google Drive account before continuing."
                )
                return False

        # Archive folder page: must select a folder
        elif current_id == self.PAGE_ARCHIVE:
            if not self._archive_path:
                QMessageBox.warning(
                    self,
                    "Folder Required",
                    "Please select an archive folder before continuing."
                )
                return False

        return True

    def accept(self) -> None:
        """Handle wizard completion - save configuration."""
        # Save all settings to config
        self.config.is_connected = True
        self.config.account_email = self._account_email
        self.config.archive_path = self._archive_path
        self.config.filter_mode = "size" if self.radioFilterBySize.isChecked() else "date"
        self.config.min_size_mb = self.spinMinSize.value()
        self.config.before_date = self.dateBeforeDate.date().toString("yyyy-MM-dd")
        self.config.dry_run = self.chkDryRun.isChecked()
        self.config.trash_after = self.chkTrashAfter.isChecked()

        self.config.save()

        super().accept()
