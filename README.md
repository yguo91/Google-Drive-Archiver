# Google Drive Archiver

A Windows desktop application that helps you free up Google Drive storage by scanning for large files, downloading them to an organized local archive, and optionally trashing the originals.

Built with **PySide6** (Qt) and the **Google Drive API**.

## Features

- **First-run setup wizard** — guides non-technical users through Google account connection and configuration
- **Smart scanning** — finds files above a configurable size threshold
- **Automatic organization** — archives files locally by type and date (e.g. `Photos/2025/2025-06/photo.jpg`)
- **Google Docs export** — converts Docs, Sheets, Slides, and Drawings to Office formats before archiving
- **Dry-run mode** — preview what would happen without making any changes
- **Download verification** — validates files before trashing originals
- **Background processing** — scan and archive run in worker threads, keeping the UI responsive

## Prerequisites

- Python 3.10+
- A Google Cloud project with the **Drive API** enabled
- An OAuth 2.0 **Desktop** client credential (`credentials.json`)

## Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/yguo91/Google-Drive-Archiver.git
   cd Google-Drive-Archiver
   ```

2. **Create a virtual environment and install dependencies**

   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Add your Google OAuth credentials**

   Place your `credentials.json` file (downloaded from the Google Cloud Console) in the project root. This file is git-ignored and must **never** be committed.

4. **Run the application**

   ```bash
   python main.py
   ```

   On first launch the onboarding wizard will walk you through connecting your Google account and choosing an archive folder.

## Project Structure

```
├── app/            # GUI layer (main window, wizard, settings dialog)
├── core/           # Business logic (file classification, organization, planning)
├── infra/          # Infrastructure (Google auth, Drive API client, filesystem)
├── storage/        # Configuration management
├── workers/        # Background scan & archive workers
├── Docs/           # Design documents
├── Icon/           # Application icons
├── main.py         # Entry point
└── requirements.txt
```

## Configuration

Settings are stored in `%APPDATA%\DriveArchiver\config.json` and can be changed through the in-app settings dialog:

| Setting | Default | Description |
|---------|---------|-------------|
| Archive folder | *(set during setup)* | Local directory for archived files |
| Minimum file size | 200 MB | Only files larger than this are shown |
| Dry run | On | Preview mode — no files are moved or deleted |
| Trash after download | On | Move originals to Drive trash after archiving |

## License

This project is for personal use.
