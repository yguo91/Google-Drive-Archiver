**UI Contract**

**0) Config keys (define once, use everywhere)**

Use these keys consistently across wizard + main window + settings:

|**Key**|**Type**|**Meaning**|**Default**|
| :- | :- | :- | :- |
|drive.connected|bool|Google Drive auth is valid|false|
|drive.account\_email|str|connected account email|""|
|archive.path|str|local archive folder|""|
|rules.min\_size\_mb|int|scan threshold|200|
|rules.dry\_run|bool|simulate only|true|
|rules.trash\_after|bool|move originals to Trash after download|true|

-----
**1) wizard\_onboarding.ui — Setup Wizard Contract**

**QWizard: Wizard**

**Role:** first-run configuration.\
**Exit condition:** when finished, you **persist config** and proceed to main window.

**pageWelcome**

**chkUnderstandTrash (QCheckBox)**

- **Controls:** “user acknowledged destructive action”
- **Signals to handle:** toggled(bool) (or stateChanged(int))
- **Behavior:**
  - If unchecked → disable wizard **Next**
  - If checked → enable **Next**
- **Config:** no direct write (it’s only a gate)

Implementation note: easiest is override page completion (e.g., isComplete() / emit completeChanged) or set a custom validation in code.

-----
**pageConnect**

**btnConnectDrive (QPushButton)**

- **Action:** start OAuth / sign-in
- **Signal:** clicked()
- **On success:** set and persist
  - drive.connected = true
  - drive.account\_email = "<email>"
- **UI updates:**
  - enable **Next**
  - update lblConnectStatus

**lblConnectStatus (QLabel)**

- **Displays:** connection status text
- **Updated by:** connect flow results
  - “Not connected”
  - “Connecting…”
  - “Connected as xxx”
  - “Failed: …”
-----
**pageArchiveFolder**

**btnBrowseArchive (QPushButton)**

- **Action:** open folder picker
- **Signal:** clicked()
- **Writes config:** archive.path

**txtArchiveFolder (QLineEdit, readOnly)**

- **Displays:** selected archive folder path
- **Updated by:** browse action or default detection
- **Reads config:** archive.path

**lblDiskFree (QLabel)**

- **Displays:** “Free space: …”
- **Updated by:** when archive.path changes
- **No config**

**Validation rule (recommended):**

- Require archive.path non-empty before allowing Next.
-----
**pageRules**

**spinMinSize (QSpinBox)**

- **Controls:** minimum file size threshold (MB)
- **Signal:** valueChanged(int)
- **Writes config:** rules.min\_size\_mb

**chkDryRun (QCheckBox)**

- **Controls:** dry run toggle
- **Signal:** toggled(bool)
- **Writes config:** rules.dry\_run

**chkTrashAfter (QCheckBox)**

- **Controls:** trash originals toggle
- **Signal:** toggled(bool)
- **Writes config:** rules.trash\_after

**Finish behavior:**

- Persist all config keys
- Launch main window
-----
**2) main\_window.ui — Main Window Contract**

**Command buttons**

**btnOpenSettings (QPushButton)** *(typo in objectName)*

- **Action:** open dlgSettings
- **Signal:** clicked()
- **On accept:** reload config + refresh UI labels

**btnScan (QPushButton)**

- **Action:** scan Google Drive for files meeting rules
- **Signal:** clicked()
- **Preconditions:**
  - drive.connected == true
  - archive.path exists/valid (local folder)
- **Reads config:**
  - rules.min\_size\_mb
  - rules.dry\_run (affects later archive behavior, not scan)
- **Updates:**
  - tblFiles rows
  - lblFilesFound
  - lblSpaceToFree
- **Recommended UX:**
  - disable Scan while scanning
  - show status text somewhere (optional future: status bar)

**btnArchiveAll (QPushButton)**

- **Action:** run archive pipeline for all items in results
- **Signal:** clicked()
- **Reads config:**
  - archive.path
  - rules.dry\_run
  - rules.trash\_after
- **Updates:**
  - progress UI (future)
  - maybe mark rows “Archived” (future)

**btnArchiveSelected (QPushButton)**

- **Action:** archive only selected rows
- **Signal:** clicked()
- **Reads config:** same as ArchiveAll
- **Reads selection from:** tblFiles.selectedItems() or selected rows
-----
**“Current Settings” display labels (always reflect config)**

**lblAccountEmail (QLabel)**

- **Display:** drive.account\_email (or “Not connected”)
- **Updated when:** app starts / after connect / after settings changes

**lblArchiveFolder (QLabel)**

- **Display:** archive.path

**lblMinSize (QLabel)**

- **Display:** rules.min\_size\_mb formatted as "200 MB"

**lblDryRun (QLabel)**

- **Display:** "On" if rules.dry\_run else "Off"

**lblTrashAfter (QLabel)**

- **Display:** "On" if rules.trash\_after else "Off"
-----
**Scan summary labels**

**lblFilesFound (QLabel)**

- **Display:** count of scan results

**lblSpaceToFree (QLabel)**

- **Display:** sum of sizes of scan results
-----
**Results table**

**tblFiles (QTableWidget)**

- **Purpose:** show scanned file list
- **Columns:** File Name | Size | Type | Date
- **Data model recommendation (very useful):**
  - Store file\_id in a hidden column **or** in the first column item’s Qt.UserRole
  - Also store raw size bytes in Qt.UserRole to avoid parsing UI strings

**Selection usage (for ArchiveSelected):**

- Determine selected rows
- Map row → file\_id → archive pipeline
-----
**3) settings\_dialog.ui — Settings Dialog Contract**

**Storage**

**btnBrowseArchive (QPushButton)**

- **Action:** choose folder
- **Signal:** clicked()
- **Updates:** txtArchivePath
- **Pending write:** to config on OK

**txtArchivePath (QLineEdit, readOnly)**

- **Displays:** candidate/new archive.path
-----
**Rules**

**spinMinSizeMb (QSpinBox)**

- **Controls:** rules.min\_size\_mb
- **Signal:** valueChanged(int) (optional live preview)
- **Pending write:** on OK

**chkDryRun (QCheckBox)**

- **Controls:** rules.dry\_run
- **Signal:** toggled(bool)
- **Pending write:** on OK

**chkTrashAfter (QCheckBox)**

- **Controls:** rules.trash\_after
- **Signal:** toggled(bool)
- **Pending write:** on OK
-----
**Buttons**

**buttonBox (QDialogButtonBox: Ok | Cancel)**

- **Signals:**
  - accepted() → validate + save config + accept()
  - rejected() → reject()

**Validation rules (recommended):**

- archive.path must not be empty
- rules.min\_size\_mb must be >= 1 (or your minimum)
-----
**4) Lifecycle flow (how everything fits)**

1. App start → load config
1. If missing essential keys or drive.connected == false → show **Wizard**
1. Wizard Finish → save config → open **Main Window**
1. Main Window “Settings…” → open **Settings Dialog**
1. Settings OK → save config → refresh main labels
1. Scan → populate table + summary
1. Archive → obey dry run + trash rules

