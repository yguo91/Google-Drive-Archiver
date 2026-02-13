"""
Google Drive Archive & Cleanup Tool

A desktop application that scans Google Drive for large files,
downloads them to an organized local archive, and moves originals to Trash.

Usage:
    python main.py

On first run, the setup wizard will guide you through:
1. Connecting your Google Drive account
2. Selecting a local archive folder
3. Configuring archive rules

Subsequent runs will show the main window directly.
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from storage.config import Config, get_credentials_path
from infra.auth import is_authenticated


def check_credentials() -> bool:
    """Check if credentials.json exists and show setup instructions if not."""
    creds_path = get_credentials_path()

    if creds_path.exists():
        return True

    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setWindowTitle("Setup Required")
    msg.setText("Google API credentials not found")
    msg.setInformativeText(
        "To use this app, you need to set up Google API credentials:\n\n"
        "1. Go to https://console.cloud.google.com/\n"
        "2. Create a new project\n"
        "3. Enable the Google Drive API\n"
        "4. Create OAuth 2.0 credentials (Desktop app)\n"
        "5. Download the credentials JSON file\n"
        "6. Save it as 'credentials.json' in the app folder\n\n"
        "Then restart the application."
    )
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.exec()

    return False


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Drive Archiver")
    app.setOrganizationName("DriveArchiver")

    # Load configuration
    config = Config()

    # Check for credentials
    if not check_credentials():
        return 1

    # Determine which window to show
    if not config.is_connected or not is_authenticated():
        # First run or not authenticated - show wizard
        from app.onboarding_wizard import OnboardingWizard

        wizard = OnboardingWizard(config)
        result = wizard.exec()

        if result != wizard.DialogCode.Accepted:
            # User cancelled wizard
            return 0

        # Reload config after wizard
        config.load()

    # Show main window
    from app.main_window import MainWindow

    window = MainWindow(config)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
