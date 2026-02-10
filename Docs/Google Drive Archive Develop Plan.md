**Google Drive Archive & Cleanup Tool**

**Development Plan (Python + PySide6)**

**Target Platform:** Windows 11\
**Primary Users:** Non-technical end users (family use)\
**Developer Stack:** Python + PySide6 (Qt)\
**Distribution Goal:** Single executable / installer

-----
**1. Project Objectives**

**1.1 Functional Goal**

Create a desktop GUI application that:

- Scans Google Drive for large files
- Downloads selected files efficiently
- Organizes them locally by **file type → year → month**
- Verifies download integrity
- Moves originals to **Google Drive Trash**
- Provides clear progress and summary feedback

**1.2 UX Goal**

- Safe defaults
- Minimal cognitive load
- Wizard-based first-run setup
- One-click repeat usage
- No technical terminology exposed to the user
-----
**2. Architectural Principles**

1. **Strict separation of concerns**
   1. UI ≠ business logic ≠ infrastructure
1. **Background execution**
   1. No long-running tasks on UI thread
1. **Two-phase safety model**
   1. Download & verify → then trash
1. **Configuration via GUI**
   1. JSON used internally only
1. **Fail-safe behavior**
   1. Never permanently delete automatically
-----
**3. Technology Stack**

|**Layer**|**Technology**|
| :- | :- |
|GUI|PySide6 (Qt 6)|
|UI Design|Qt Designer (.ui files)|
|Drive API|Google Drive API (Python SDK)|
|Background Jobs|QThreadPool + QRunnable|
|Config|JSON|
|State Tracking|SQLite|
|Logging|Rotating file logs|
|Packaging|PyInstaller|

-----
**4. Project Structure**

drive-archiver/

├─ app/                  # Application entry & UI

├─ core/                 # Domain logic

├─ infra/                # External integrations (Drive, FS)

├─ storage/              # Config, state, logs

├─ workers/              # Background tasks

├─ resources/            # Icons, styles

├─ tests/                # Unit tests (optional)

└─ README.md

-----
**5. Functional Modules**

**5.1 UI Layer (app/ui)**

**Responsibilities**

- Display wizard and main screens
- Collect user input
- Show progress & results
- Dispatch background jobs

**Components**

- Setup Wizard (first run)
- Main Window
- Progress Dialog
- Result Summary Dialog
-----
**5.2 Core Logic (core)**

**Responsibilities**

- Business rules
- File classification
- Archive planning
- Execution orchestration

**Key Modules**

- domain.py — data models
- classifier.py — file type mapping
- organizer.py — folder rules (type/year/month)
- planner.py — eligibility & filtering
- executor.py — download → verify → trash
- verify.py — integrity checks
- errors.py — domain exceptions
-----
**5.3 Infrastructure (infra)**

**Responsibilities**

- External systems & APIs

**Key Modules**

- auth.py — Google OAuth handling
- drive\_client.py — Drive list/download/trash
- export.py — Docs/Sheets/Slides export
- filesystem.py — safe writes, atomic moves
- net.py — retry/backoff logic
-----
**5.4 Background Workers (workers)**

**Responsibilities**

- Run long tasks without blocking UI

**Workers**

- ScanWorker
- ArchiveWorker

**Communication**

- Qt signals:
  - progress
  - status
  - finished
  - error
-----
**5.5 Storage (storage)**

**Responsibilities**

- Persistent app data

**Components**

- config.json — user settings
- state.db — archived file tracking
- log files — per run, timestamped

**Location**

- %APPDATA%\DriveArchiver\
-----
**6. User Workflow**

**6.1 First Run (Setup Wizard)**

1. Welcome & explanation
1. Google Drive connection
1. Local archive folder selection
1. Basic rules:
   1. Minimum file size
   1. Dry run
   1. Trash originals
-----
**6.2 Regular Use**

1. Launch app
1. Click **Scan**
1. Review file list & summary
1. Click **Archive**
1. View result summary
-----
**7. File Eligibility Rules**

- Owned by signed-in user
- Located in “My Drive”
- File size ≥ user-defined threshold
- Not previously archived (state DB)
-----
**8. Local Folder Organization**

<ArchiveRoot>\

├─ Photos\YYYY\YYYY-MM\

├─ Videos\YYYY\YYYY-MM\

├─ Documents\YYYY\YYYY-MM\

├─ Audio\

├─ Archives\

├─ Installers\

└─ Other\

**Date Source Priority**

1. Modified time
1. Created time
-----
**9. Safety & Data Protection**

**Two-Phase Execution**

1. Download file
1. Verify integrity
1. Move to final path
1. Update state DB
1. Move original to Drive Trash (optional)

**Dry Run Mode**

- Preview only
- No data modification
-----
**10. Error Handling Strategy**

|**Internal Error**|**User Message**|
| :- | :- |
|Auth error|“Please connect Google Drive.”|
|Network error|“Connection issue. Try again later.”|
|Disk full|“Not enough space in archive folder.”|
|Download failure|“File skipped. Original not moved.”|

No stack traces shown to end users.

-----
**11. Development Milestones**

1. Project scaffold + logging
1. Setup Wizard UI + config persistence
1. Google Drive authentication
1. Scan pipeline (preview only)
1. File classification & organizer
1. Archive pipeline (download + verify)
1. Trash integration
1. Progress & summary UI
1. State tracking
1. Packaging & installer
-----
**12. Post-v1 Enhancements (Optional)**

- Folder exclusion rules
- Date-based filters
- Scheduler
- Restore assistant
- UI polish
-----
**13. Final Notes**

This plan prioritizes:

- correctness
- safety
- clarity
- non-technical usability

It is intentionally conservative and scalable.

