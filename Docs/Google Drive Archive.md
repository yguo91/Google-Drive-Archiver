**Google Drive Archive & Cleanup Tool**

**Design Document (v1.0)**

**1. Purpose & Scope**

**1.1 Problem Statement**

Google Drive provides only **15 GB of free storage**. Manually downloading large files via browser is:

- slow and unreliable
- inefficient for bulk operations
- results in poorly organized local storage

This tool automates:

- identifying large files on Google Drive
- downloading them efficiently
- organizing them locally by **file type + year/month**
- moving originals to **Google Drive Trash** after successful download

**1.2 Target Users**

- **Primary:** Non-technical end users (e.g., spouse)
- **Secondary:** Power users (developer)

Each user:

- has their **own PC**
- has their **own Google account**

**1.3 Out of Scope (v1)**

- Permanent deletion
- Sync back to Drive
- Background scheduler
- Deduplication
- Shared Drives / Shared-with-me files
-----
**2. Platform & Architecture Decisions**

|**Area**|**Decision**|
| :- | :- |
|OS|Windows 11|
|Accounts|One Google account per PC|
|App Type|Desktop GUI application|
|Tech Stack (recommended)|Python + PySide6 (Qt)|
|Distribution|Single executable / installer|
|Storage|Per-user AppData|

-----
**3. Core Functional Requirements**

**Must Have**

- GUI-based onboarding and setup
- Google Drive authentication
- Scan Drive for eligible files
- Preview (dry run)
- Download + local organization
- Verify download success
- Move originals to Trash
- Progress & summary report

**Should Have**

- Configurable minimum file size
- Folder picker for local archive
- Export Google Docs formats
- Log file per run
-----
**4. First-Run Setup Wizard (Initial Process)**

**Design Goal**

Allow a **non-programmer** to complete setup in under **2 minutes** with safe defaults.

-----
**Step 1 — Welcome**

**Text (plain language):**

- “This tool scans Google Drive for large files”
- “Downloads them to your PC in an organized archive”
- “Moves originals to Trash after download”

**Controls:**

- Checkbox: *I understand files will be moved to Trash*
- Button: **Next**
-----
**Step 2 — Connect Google Drive**

**Controls:**

- Button: **Connect Google Drive**
- Status label: Connected as: user@gmail.com

**Rule:** Cannot proceed unless connected.

-----
**Step 3 — Choose Local Archive Folder**

**Default path:**

- D:\DriveArchive (if D exists)
- else C:\DriveArchive

**Controls:**

- Folder picker (Browse…)
- Optional: disk free space display
- Button: **Next**
-----
**Step 4 — Basic Rules**

**Controls:**

- Minimum file size (number input, default **200 MB**)
- Toggle: **Dry run first** (default ON)
- Toggle: **Move originals to Trash after download** (default ON)
- Button: **Finish**
-----
**5. Main Application UI**

**Primary Screen Elements**

- Connected Google account email
- Archive folder path
- Minimum file size
- Toggle status (Dry run / Trash enabled)
- Button: **Scan Google Drive**

**After Scan**

- Summary:
  - Files found
  - Estimated space to free
- List view:
  - File name | Size | Type | Date
- Buttons:
  - **Archive All**
  - **Archive Selected**
-----
**6. File Eligibility Rules**

**Included**

- Files owned by the user
- Files in **My Drive**
- File size ≥ user-defined threshold

**Excluded**

- Shared-with-me files
- Google system folders
- Files already archived (tracked via state)
-----
**7. Local Folder Organization Rules**

**Structure**

<ArchiveRoot>\

├─ Photos\

│  └─ YYYY\

│     └─ YYYY-MM\

├─ Videos\

├─ Documents\

├─ Audio\

├─ Archives\

├─ Installers\

└─ Other\

**Date Source Priority**

1. Google Drive modifiedTime
1. fallback: createdTime
-----
**8. File Type Classification**

|**Category**|**Extensions**|
| :- | :- |
|Photos|jpg, jpeg, png, heic, webp, gif|
|Videos|mp4, mkv, mov, avi, webm|
|Audio|mp3, wav, flac, m4a|
|Documents|pdf, docx, doc, xlsx, pptx, txt|
|Archives|zip, rar, 7z, tar, gz|
|Installers|exe, msi|
|Other|all remaining|

**Google Native Files**

|**Type**|**Export As**|
| :- | :- |
|Docs|PDF|
|Sheets|XLSX|
|Slides|PDF|

-----
**9. Safety & Data Protection Model**

**Two-Phase Execution**

**Phase 1: Download**

- Download file
- Verify:
  - file exists
  - file size > 0
- Log success

**Phase 2: Cleanup**

- Only after successful verification
- Move original file to **Google Drive Trash**
- Never permanently delete automatically
-----
**10. Dry Run Mode**

**Purpose**

- Training wheels for first-time users
- Prevents accidental data loss

**Behavior**

- Scan + preview only
- No download
- No trash action
- Clear message: *“No files were changed.”*
-----
**11. Logging & State Tracking**

**Storage Locations**

- Config:
  - %APPDATA%\DriveArchiver\config.json
- Logs:
  - %APPDATA%\DriveArchiver\logs\YYYY-MM-DD.log
- State (optional):
  - %APPDATA%\DriveArchiver\state.db

**Log Contents**

- Timestamp
- File ID
- File name
- Size
- Local destination
- Action result
-----
**12. UX Language Guidelines**

Avoid technical terms:

- ❌ OAuth, API, threshold
- ✅ Connect, Scan, Archive, Minimum size, Move to Trash

Tone:

- calm
- reassuring
- explicit about actions
-----
**13. Error Handling (User-Friendly)**

|**Situation**|**Message**|
| :- | :- |
|Not connected|“Please connect Google Drive first.”|
|No files found|“No files match your criteria.”|
|Download failed|“File skipped. Original was not moved.”|
|Network issue|“Connection issue. Try again later.”|

-----
**14. Future Enhancements (Post-v1)**

- Folder exclusion rules
- Age-based filtering
- Scheduler
- Restore assistant
- Multi-account switcher
-----
**15. Summary**

This design delivers:

- **One-click experience**
- **Safe defaults**
- **Clear GUI**
- **Non-technical usability**
- **Scalable local organization**

It is intentionally minimal, safe, and shareable.

