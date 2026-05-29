# Cursor Technical Development Plan: Media Management App

This document is designed to be fed directly into Cursor or another AI coding assistant to guide the step-by-step development of the Media Management Desktop Application.

## 1. Project Context & Constraints

*   **Goal:** Build a Windows 11 desktop application that acts as a **central catalog** for media and download files spread across **multiple library roots** on **different storage devices** (local SSD/HDD, NAS, DAS, USB). The app should index files in place, detect cross-device duplicates via hashing, track download/source metadata, and handle **offline or unavailable** volumes gracefully.
*   **Target Platform:** Windows 11 (Desktop).
*   **Key Scenario:**
    *   Files may live in different root folders (not one single download directory).
    *   Files may reside on different devices: NAS, DAS, internal HDD, SSD, removable USB.
    *   Some devices may be **offline** at any given time — the catalog must remain usable.
    *   Subfolders under each root are common; scanning must be **recursive**.
*   **Primary User Workflow (RAR → Extract):**
    1. Download content as a **RAR archive** (with or without password).
    2. Decompress on a **local device** (SSD/HDD).
    3. The extracted folder always uses a special naming pattern: **`[Original Name]`** (bracket-wrapped canonical name).
    4. The app should **not hash everything by default** — full SHA-256 is expensive on large libraries and NAS files.
    5. Instead: on scan/ingest, match by **same or similar `[Original Name]`** against the catalog, **highlight candidates**, and let the user **decide whether to run hash verification**.
*   **Duplicate Detection Strategy (Two-Tier):**
    *   **Tier 1 — Soft match (default, low cost):** Compare normalized `[Original Name]` across extraction folders; fuzzy match for typos/variants. No file reading beyond folder listing.
    *   **Tier 2 — Hash verify (user-triggered):** SHA-256 only when user clicks "Verify with Hash" on a highlighted group. Confirms byte-identical content.
*   **Design Principle — Catalog vs Storage:**
    *   **SQLite catalog** (stored locally on SSD) = source of truth for metadata, always available.
    *   **Physical files** = may be on NAS/network share or unplugged drives; indexed in place, not moved by default.
    *   **Sidecar JSON** = optional export/backup layer; primary metadata lives in SQLite (especially for NAS files where sidecar writes are slow).
*   **Tech Stack:**
    *   Python 3.10+
    *   `PyQt6` (GUI Framework)
    *   `sqlite3` (Internal Database — WAL mode recommended)
    *   `hashlib` (SHA-256 for duplicate detection)
    *   `shutil` / `os` / `pathlib` (File operations)
    *   `Pillow` (EXIF / image metadata — later phases)
*   **Coding Standards:**
    *   Strict type hinting (`typing` module).
    *   Modular architecture (Separate GUI from business logic).
    *   Asynchronous operations or `QThread` / `QThreadPool` for heavy file scanning to prevent GUI freezing.
    *   Error handling with logging (do not crash on corrupted media, permission errors, or offline paths).
    *   Never block the main GUI thread during hash or network scan operations.

## 2. Recommended Directory Structure

Ask Cursor to create the following structure initially:

```text
/media_manager
│── /src
│   │── main.py                 # Application entry point
│   │── /gui                    # PyQt6 windows and widgets
│   │   │── main_window.py
│   │   │── ingest_dialog.py
│   │   │── detail_panel.py     # Metadata editor for selected file
│   │   │── device_panel.py     # Storage device / root list
│   │   │── duplicate_dialog.py # Cross-device duplicate review
│   │   │── reorganize_dialog.py # Preview + confirm flatten/rename
│   │   └── folder_tree.py      # Optional: folder navigation within a root
│   │── /core                   # Business logic
│   │   │── database.py         # SQLite schema & CRUD
│   │   │── device_manager.py   # Online/offline detection, volume IDs
│   │   │── scanner.py          # Recursive traversal, hashing, file type detection
│   │   │── ingestion.py        # Multi-root scan pipeline
│   │   │── duplicate_finder.py # Hash-based duplicate grouping (Tier 2)
│   │   │── name_matcher.py     # [Original Name] soft match (Tier 1)
│   │   │── archive_tracker.py  # RAR archive → extraction folder linking
│   │   │── reorganize.py       # Flatten, rename, [Original Details] capture
│   │   │── file_ops.py         # Safe move/rename, sidecar JSON, relink roots
│   │   └── metadata.py         # EXIF / media info extraction (later)
│   └── /utils
│       │── config.py           # App config (catalog path, library roots)
│       └── logging.py
│── /data                       # Default location for local catalog DB
│── requirements.txt
└── README.md
```

## 3. Database Schema (Multi-Device)

The catalog database (`catalog.db`) should live on **local SSD** (e.g. `%APPDATA%/MediaManager/catalog.db`), not on NAS.

### 3.1 `StorageDevice`

Represents a physical or network storage unit.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | |
| `name` | TEXT | User label, e.g. "Synology NAS", "Local SSD" |
| `type` | TEXT | `ssd`, `hdd`, `nas`, `das`, `usb`, `unknown` |
| `identifier` | TEXT | Stable ID: volume serial, UNC root, or user-defined UUID |
| `mount_hint` | TEXT | Last known path: `D:\`, `\\NAS\share`, `E:\` |
| `is_online` | BOOLEAN | Updated on startup and before scans |
| `last_seen` | DATETIME | Last time device was reachable |
| `notes` | TEXT | Optional |

### 3.2 `LibraryRoot`

A folder on a device that the app indexes recursively.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | |
| `device_id` | INTEGER FK | → `StorageDevice.id` |
| `root_path` | TEXT | Absolute path at last scan |
| `label` | TEXT | e.g. "NAS Downloads", "D: Archive" |
| `enabled` | BOOLEAN | Include in scans |
| `last_scan` | DATETIME | |
| `file_count` | INTEGER | Cached count from last scan |

### 3.3 `Media`

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | |
| `root_id` | INTEGER FK | → `LibraryRoot.id` |
| `relative_path` | TEXT | Path inside root, e.g. `site-a/video1.mp4` |
| `absolute_path` | TEXT | Cached full path (may go stale if drive letter changes) |
| `folder_path` | TEXT | Parent folder relative to root, e.g. `site-a` |
| `depth` | INTEGER | 0 = file in root, 1+ = subfolder depth |
| `original_name` | TEXT | Filename at first ingest |
| `file_hash` | TEXT | SHA-256, indexed |
| `file_size` | INTEGER | Bytes, indexed |
| `file_type` | TEXT | `image`, `video`, `archive`, `document`, `other` |
| `mime_type` | TEXT | Optional |
| `mtime` | DATETIME | File modification time (for incremental scan) |
| `availability` | TEXT | `online`, `offline`, `missing` |
| `status` | TEXT | `new`, `indexed`, `duplicate`, `error` |
| `date_added` | DATETIME | When first indexed |
| `last_verified` | DATETIME | Last time file existence was confirmed |

**Indexes:** `file_hash`, `file_size`, `root_id`, `availability`, `(root_id, relative_path)` UNIQUE.

### 3.4 `Metadata`

| Column | Type | Notes |
|--------|------|-------|
| `media_id` | INTEGER PK/FK | → `Media.id` |
| `source_url` | TEXT | Original download URL |
| `source_site` | TEXT | e.g. `youtube.com` |
| `source_id` | TEXT | Post/video ID if known |
| `original_filename` | TEXT | Name at download time |
| `download_tool` | TEXT | browser, IDM, aria2, torrent, manual |
| `download_date` | DATETIME | When downloaded (user or extracted) |
| `description` | TEXT | |
| `tags` | TEXT | Comma-separated or JSON array |
| `notes` | TEXT | User notes |
| `custom_fields` | TEXT | JSON blob for site-specific data |
| `original_details` | TEXT | JSON — see section 3.12 `[Original Details]` |

### 3.5 `DownloadHistory`

Track path changes, re-downloads, and relinks.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | |
| `media_id` | INTEGER FK | → `Media.id` |
| `event_type` | TEXT | `ingested`, `moved`, `renamed`, `relinked`, `marked_missing`, `reorganized` |
| `old_path` | TEXT | |
| `new_path` | TEXT | |
| `timestamp` | DATETIME | |
| `details` | TEXT | Optional JSON |

### 3.6 `ExtractionFolder`

Represents one decompressed `[Original Name]` folder — the primary unit for Tier 1 matching.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | |
| `root_id` | INTEGER FK | → `LibraryRoot.id` |
| `folder_path` | TEXT | Relative path to folder, e.g. `[Cool Video]/` |
| `original_name` | TEXT | Parsed name inside brackets, e.g. `Cool Video` |
| `normalized_name` | TEXT | Lowercased, trimmed, punctuation-normalized — **indexed** |
| `file_count` | INTEGER | Files inside folder (from light scan) |
| `total_size` | INTEGER | Sum of file sizes inside folder |
| `date_indexed` | DATETIME | |
| `availability` | TEXT | `online`, `offline`, `missing` |
| `new_folder_name` | TEXT | Assigned `[New Folder Name]` after user confirms item is new |
| `reorganize_status` | TEXT | `pending`, `preview`, `completed`, `skipped`, `error` |
| `reorganized_at` | DATETIME | When flatten+rename last ran |

**Indexes:** `normalized_name`, `(root_id, folder_path)` UNIQUE.

### 3.7 `Archive`

Optional link from downloaded RAR to extracted folder.

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | |
| `media_id` | INTEGER FK | → `Media.id` (the `.rar` file) |
| `extraction_id` | INTEGER FK | → `ExtractionFolder.id` (nullable until extracted) |
| `has_password` | BOOLEAN | User flag |
| `extracted_at` | DATETIME | |
| `notes` | TEXT | Password hint storage — **never store actual password in DB** |

### 3.8 `NameMatchGroup` / `NameMatchMember` (Tier 1 — Soft Match)

Groups extraction folders with same or similar `[Original Name]`. Hash not required.

| Table | Column | Notes |
|-------|--------|-------|
| `NameMatchGroup` | `id` | PK |
| | `normalized_name` | Canonical normalized name for group |
| | `match_type` | `exact`, `similar` |
| | `similarity_score` | 0.0–1.0 (1.0 = exact); NULL if exact |
| | `member_count` | |
| | `review_status` | `pending`, `dismissed`, `confirmed_different`, `sent_to_hash` |
| | `reviewed_at` | DATETIME |
| `NameMatchMember` | `group_id` FK | |
| | `extraction_id` FK | → `ExtractionFolder.id` |
| | `is_primary` | User-chosen reference copy |

### 3.9 `DuplicateGroup` / `DuplicateMember` (Tier 2 — Hash Confirmed)

Link files or folders that share the same hash after user-triggered verification.

| Table | Purpose |
|-------|---------|
| `DuplicateGroup` | `id`, `file_hash`, `file_size`, `member_count`, `source_name_group_id` (FK → `NameMatchGroup`, nullable), `reviewed` |
| `DuplicateMember` | `group_id` FK, `media_id` FK (nullable), `extraction_id` FK (nullable), `is_primary` |

### 3.10 `[Original Name]` Parsing Rules

Folder names follow the pattern `[Original Name]`:

| Raw folder name | `original_name` | `normalized_name` |
|-----------------|-----------------|-------------------|
| `[Cool Video]` | `Cool Video` | `cool video` |
| `[Cool Video (2024)]` | `Cool Video (2024)` | `cool video 2024` |
| `[Cool Video] (1)` | `Cool Video` | `cool video` (strip copy suffix outside brackets) |

**Normalization steps:** strip outer brackets → lowercase → collapse whitespace → remove/copy-suffix patterns like `(1)`, `(2)` → optional strip punctuation for fuzzy key.

**Similarity (Tier 1):** use `rapidfuzz` ratio on `normalized_name`; default threshold **≥ 0.85** = similar, **1.0** = exact. Configurable in `config.json`.

### 3.11 Example Config (`config.json`)

```json
{
  "catalog_db": "C:\\Users\\You\\AppData\\MediaManager\\catalog.db",
  "library_roots": [
    { "device_name": "Local SSD", "device_type": "ssd", "path": "C:\\Downloads", "label": "PC Downloads" },
    { "device_name": "Local HDD", "device_type": "hdd", "path": "D:\\Media", "label": "D Drive Archive" },
    { "device_name": "Synology NAS", "device_type": "nas", "path": "\\\\NAS\\share\\downloads", "label": "NAS Downloads" }
  ],
  "scan": {
    "skip_extensions": [".crdownload", ".part", ".tmp", ".aria2"],
    "media_extensions": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".mkv", ".avi", ".mov", ".zip", ".rar"],
    "extraction_folder_pattern": "^\\[(.+)\\]$",
    "hash_on_scan": false,
    "hash_chunk_size": 65536,
    "parallel_local_workers": 2,
    "parallel_network_workers": 1
  },
  "name_matching": {
    "similarity_threshold": 0.85,
    "highlight_exact": true,
    "highlight_similar": true,
    "auto_hash_on_exact": false
  },
  "reorganize": {
    "folder_wrapper": "[{new_folder_name}]",
    "filename_template": "{filetype}_{new_folder_name}_{seq:04d}_{hash8}{ext}",
    "hash_in_filename": "first_8_chars",
    "sequence_rule": "root_files_first_then_subfolders_by_path",
    "delete_empty_subfolders": true,
    "skip_files": [".DS_Store", "Thumbs.db", "desktop.ini"],
    "max_filename_length": 200,
    "preview_required": true
  }
}
```

### 3.12 `[Original Details]` Metadata

Captured **before** flatten/rename destroys the original folder layout. Stored in `Metadata.original_details` and optional sidecar JSON.

```json
{
  "original_relative_path": "clips/part1/sub/sample.mp4",
  "original_filename": "sample.mp4",
  "original_absolute_path": "D:\\Extract\\[Cool Video]\\clips\\part1\\sub\\sample.mp4",
  "sequence_no": 15,
  "sequence_rule": "root_files_first_then_subfolders_by_path",
  "captured_at": "2026-05-29T12:00:00Z"
}
```

### 3.13 `[New Folder Name]` Generation

When user confirms an extraction is **new** (not a duplicate), assign a canonical `[New Folder Name]` for the folder.

**Priority order (user can override at prompt):**

| Priority | Source | Example |
|----------|--------|---------|
| 1 | **Manual input** | User types `Cool Video 2024` → `[Cool Video 2024]` |
| 2 | Cleaned `[Original Name]` | `[Cool Video (1)]` → `Cool Video` |
| 3 | Linked RAR filename | `CoolVideo.rar` → `CoolVideo` |
| 4 | Metadata title / source | From `source_url` or user tags |
| 5 | Template | Config pattern, e.g. `{date}_{original_name}` |

**Sanitization for filesystem use (`safe_new_folder_name`):**
- Remove Windows-invalid chars: `\ / : * ? " < > |`
- Collapse whitespace; trim trailing dots/spaces
- Optional max length (e.g. 80 chars) before wrapping in brackets
- Folder on disk: `[Cool Video 2024]` (brackets preserved per user convention)

### 3.14 Flatten & Rename Rules (New Item Workflow)

Triggered when user marks extraction as **new** and clicks **Reorganize**.

**Step 1 — Assign `[New Folder Name]`**  
Rename extraction folder from `[Original Name]` → `[New Folder Name]` (if different).

**Step 2 — Build file list with sequence numbers**

Order rule (`root_files_first_then_subfolders_by_path`):

1. All files **directly in folder root**, sorted A→Z by filename.
2. Then each **subfolder**, sorted A→Z by relative folder path (depth-first).
3. Within each subfolder, files sorted A→Z by filename.

Example:

```text
[Cool Video]/
├── cover.jpg              → seq 001
├── intro.mp4              → seq 002
├── clips/
│   ├── part1.mp4          → seq 003
│   └── part2.mp4          → seq 004
└── extras/readme.txt      → seq 005
```

**Step 3 — For each file (before any move):**
1. Compute SHA-256 hash (required for rename pattern and metadata).
2. Write `[Original Details]` to DB (and optional sidecar).
3. Generate new filename from template.

**Filename template (recommended):**

```text
{filetype}_{new_folder_name}_{seq:04d}_{hash8}{ext}
```

| Token | Example | Notes |
|-------|---------|-------|
| `{filetype}` | `VIDEO`, `IMAGE`, `DOC` | Uppercase type prefix |
| `{new_folder_name}` | `Cool_Video_2024` | Sanitized (spaces → `_`) |
| `{seq:04d}` | `0003` | 4-digit sequence |
| `{hash8}` | `a3f8b2c1` | **First 8 chars of SHA-256** (see concerns) |
| `{ext}` | `.mp4` | Original extension preserved |

Example result: `VIDEO_Cool_Video_2024_0003_a3f8b2c1.mp4`

**Step 4 — Flatten:** Move every file into `[New Folder Name]/` root (no subfolders remain).

**Step 5 — Cleanup:** Remove empty subfolders; update `ExtractionFolder`, `Media` paths, and log `DownloadHistory` event `reorganized`.

**Step 6 — Preview first:** UI must show old path → new path table; user confirms before execute (`preview_required: true`).

### 3.15 Reorganize Concerns & Safeguards

| Concern | Mitigation |
|---------|------------|
| Full 64-char hash makes filenames too long | Use `{hash8}` (first 8 chars) by default; full hash stays in DB |
| Windows MAX_PATH (260) | `max_filename_length` config; truncate `{new_folder_name}` if needed |
| Name collision after flatten | Sequence numbers + hash8 make collisions extremely unlikely |
| Losing subfolder meaning | `[Original Details]` preserves full original path |
| Cross-volume move (NAS/USB) slow | Show progress; copy-verify-delete for network targets |
| Re-run reorganize on same folder | Block if `reorganize_status=completed` unless user forces |
| Non-media junk files | `skip_files` list; optional include `.txt`/`.nfo` via config |
| Offline device | Reorganize disabled when `availability != online` |
| Hash in filename changes if file edited | Treat hash as ingest-time fingerprint; don't re-hash rename automatically |

## 4. Windows & Multi-Device Notes

*   **Prefer UNC paths for NAS** (`\\NAS\share\...`) over mapped drive letters when possible — more stable across sessions.
*   **Drive letters change** (USB/DAS): store `identifier` + `relative_path`; provide a **Relink Root** flow when mount path changes.
*   **Offline devices:** mark `StorageDevice.is_online = false` and affected `Media.availability = offline`; show greyed in UI, do not delete records.
*   **Missing files:** file was online before but path no longer exists → `availability = missing`.
*   **Incremental scan:** compare `mtime` + `file_size` before re-hashing; skip unchanged files.
*   **Network performance:** limit concurrent NAS scans; cache hashes in DB; offer "quick scan" (metadata only) vs "full scan" (hash all).
*   **Sidecar JSON:** generate on local drives by default; make NAS sidecars opt-in.
*   **Hash is opt-in:** default scan indexes folder names, file counts, and sizes only. Hash runs when user confirms a `NameMatchGroup`.

## 4.1 User Workflow: RAR Download → Extract → Soft Match → Optional Hash

```text
1. Download          CoolVideo.rar  (optional: app indexes RAR in catalog)
        ↓
2. Extract locally   →  folder: [Cool Video]/
        ↓
3. Scan / watch      App detects [Cool Video], parses original_name
        ↓
4. Tier 1 query      DB: any existing [Cool Video] or similar names?
        ↓
5. UI highlight      🟡 exact name match  /  🟠 similar name match
        ↓
6. User decides      [Dismiss] [Different item] [Verify with Hash]
        ↓
7. Tier 2 (optional) Hash files in both folders → confirm byte-identical
```

### 4.2 User Workflow: New Item → Reorganize

```text
1. Name match review     User marks item as NEW (not duplicate)
        ↓
2. Assign [New Folder Name]  Manual input or suggested from Original Name / RAR
        ↓
3. Preview               Table: original path → new flat path + new filename
        ↓
4. Capture metadata      [Original Details] saved for every file BEFORE move
        ↓
5. Hash (required here)  SHA-256 each file (needed for filename + DB)
        ↓
6. Flatten + rename      Pull subfolder files up; rename per template
        ↓
7. Rename folder         [Original Name] → [New Folder Name]
        ↓
8. Update catalog        DB paths, reorganize_status=completed
```

**UI highlight colors (suggested):**

| Status | Meaning | User action |
|--------|---------|-------------|
| 🟡 Exact name | Same `[Original Name]` already in catalog | Review → hash or dismiss |
| 🟠 Similar name | Fuzzy match ≥ threshold (e.g. 85%) | Review → hash or mark different |
| 🟢 Hash confirmed | Tier 2 verified identical content | Choose keeper / delete copy |
| ⚪ No match | New unique name | No action needed |

## 5. Step-by-Step Implementation Prompts for Cursor

**Copy and paste these phases one by one into Cursor to build the app iteratively.**

---

### Phase 1: Multi-Device Database Setup

> **Prompt for Cursor:**
> "Create `src/core/database.py` and `src/utils/config.py`. Use `sqlite3` with WAL mode for a catalog database at a configurable local path (default `%APPDATA%/MediaManager/catalog.db`).
>
> 1. Implement tables: `StorageDevice`, `LibraryRoot`, `Media`, `Metadata`, `DownloadHistory`, `ExtractionFolder`, `Archive`, `NameMatchGroup`, `NameMatchMember`, `DuplicateGroup`, `DuplicateMember` — use the schema defined in `media_manager_plan.md` section 3.
> 2. Add indexes on `Media.file_hash`, `Media.file_size`, `Media.root_id`, `Media.availability`, and UNIQUE `(root_id, relative_path)`.
> 3. Implement CRUD methods:
>    - Devices: `insert_device`, `get_devices`, `update_device_online_status`
>    - Roots: `insert_root`, `get_roots_by_device`, `update_root_scan_stats`
>    - Media: `insert_media`, `get_media_by_hash`, `get_media_by_root`, `update_media_availability`, `update_media_path`
>    - Extractions: `insert_extraction_folder`, `get_extractions_by_normalized_name`, `get_all_extractions`
>    - Name matches: `create_name_match_group`, `get_pending_name_matches`, `update_name_match_review_status`
>    - Metadata: `upsert_metadata`, `get_metadata`
>    - History: `log_event`
> 4. Load library roots from `config.json` on startup if present.
> Use strict type hints and a `Database` class wrapper."

---

### Phase 2: Device Manager & Path Utilities

> **Prompt for Cursor:**
> "Create `src/core/device_manager.py`.
>
> 1. `check_path_accessible(path) -> bool` — returns whether a path is reachable (handles offline NAS/USB).
> 2. `detect_device_info(path) -> dict` — infer device type and a stable `identifier` (volume serial via `win32api` or fallback to normalized path root).
> 3. `resolve_absolute_path(root_id) -> str | None` — resolve current mount path for a library root.
> 4. `refresh_all_device_status(db)` — update `is_online` for all devices and `availability` for media (`online` / `offline` / `missing`).
> 5. `relink_root(root_id, new_path, db)` — when user remaps a drive or NAS path, update `LibraryRoot.root_path`, recalculate `Media.absolute_path`, log to `DownloadHistory`.
> Handle permission errors and unreachable network paths gracefully with logging."

---

### Phase 3: Scanner & File Type Detection

> **Prompt for Cursor:**
> "Create `src/core/scanner.py`.
>
> 1. `calculate_hash(file_path, chunk_size=65536) -> str | None` — SHA-256 in chunks; return None on error.
> 2. `iter_media_files(root_path, extensions, skip_extensions) -> Iterator[Path]` — recursive walk with junk filtering (`.crdownload`, `.part`, `.tmp`, `Thumbs.db`).
> 3. `detect_file_type(path) -> str` — classify as image/video/archive/document/other by extension.
> 4. `file_needs_hash(path, db_record) -> bool` — incremental logic: re-hash only if mtime or size changed.
> 5. `build_relative_paths(root_path, file_path) -> tuple[str, str, int]` — returns `(relative_path, folder_path, depth)`.
> All functions must handle OS and network permission errors without raising uncaught exceptions."

---

### Phase 4: File Operations & Sidecar JSON

> **Prompt for Cursor:**
> "Create `src/core/file_ops.py`.
>
> 1. `generate_sidecar_json(file_path, metadata_dict, force=False) -> bool` — write `file.ext.json` beside the file; skip on NAS unless `force=True` or config enables it.
> 2. `safe_rename_or_move(old_path, new_path, db, media_id)` — move/rename file and optional sidecar; update `Media` paths and log `DownloadHistory`.
> 3. `show_in_explorer(file_path)` — Windows: `os.startfile` / `explorer /select,` only if file is online.
> 4. Guard all file mutations: refuse if `availability != online`.
> Handle errors gracefully with logging."

---

### Phase 5: `[Original Name]` Parser & Name Matcher (Tier 1)

> **Prompt for Cursor:**
> "Create `src/core/name_matcher.py`.
>
> 1. `parse_extraction_folder(dir_name) -> ExtractionInfo | None` — detect `[Original Name]` pattern; return `original_name` and `normalized_name` per section 3.10 rules.
> 2. `normalize_name(name) -> str` — lowercase, collapse whitespace, strip `(1)` copy suffixes, optional punctuation removal.
> 3. `find_exact_matches(normalized_name, db) -> list[ExtractionFolder]` — SQL lookup on indexed `normalized_name`.
> 4. `find_similar_matches(normalized_name, db, threshold=0.85) -> list[tuple[ExtractionFolder, float]]` — use `rapidfuzz.fuzz.ratio` against all catalog names (cache name list in memory for performance).
> 5. `create_or_update_name_match_group(db, extraction_id)` — on new folder ingest, run exact + similar search; create `NameMatchGroup` with `review_status=pending` if matches found.
> 6. `review_name_match(group_id, action)` — actions: `dismiss`, `confirmed_different`, `sent_to_hash`.
> **No hashing in this module** — folder listing and string comparison only."

---

### Phase 6: Multi-Root Ingestion Engine (Light Scan Default)

> **Prompt for Cursor:**
> "Create `src/core/ingestion.py` and `src/core/archive_tracker.py`.
>
> 1. `scan_root(root_id, db, hash_mode='never', progress_callback=None)` — recursively scan one library root:
>    - Skip if root/device offline.
>    - **Detect `[Original Name]` folders** → insert/update `ExtractionFolder` (file_count, total_size via light walk; no hash).
>    - **Detect `.rar` files** → insert `Media` + optional `Archive` row (`has_password` user-set later).
>    - For other media files inside extraction folders: index path + size + mtime only unless `hash_mode='full'`.
>    - After each new `ExtractionFolder`, call `name_matcher.create_or_update_name_match_group`.
>    - Do **not** auto-hash unless config `hash_on_scan=true`.
> 2. `scan_all_enabled_roots(db, hash_mode='never', ...)` — scan all enabled roots.
> 3. Emit progress events: `(current, total, current_item, root_label, match_found: bool)`.
> 4. Design for background execution — no GUI imports in core logic.
> 5. When name match found: log `🟡 exact` or `🟠 similar` with paths and device names."

---

### Phase 7: Hash Verification on Demand (Tier 2)

> **Prompt for Cursor:**
> "Create `src/core/duplicate_finder.py` for **user-triggered** hash verification only.
>
> 1. `verify_name_match_group(group_id, db, progress_callback)` — when user clicks 'Verify with Hash':
>    - Load all `ExtractionFolder` members in the group.
>    - For each folder: hash all files (or largest/n representative files first for quick reject).
>    - Compare file sets: same count + matching hashes per file → confirm duplicate.
>    - Create/update `DuplicateGroup` linked via `source_name_group_id`.
>    - Set `NameMatchGroup.review_status = sent_to_hash`.
> 2. `verify_single_extraction_pair(extraction_id_a, extraction_id_b, db)` — hash-compare two specific folders.
> 3. `find_hash_duplicate_groups(db)` — list confirmed hash duplicate groups.
> 4. `set_primary_duplicate(db, group_id, member_id)` — mark user's chosen keeper.
> 5. Return results with: device, path, hash status (`confirmed` / `mismatch` / `partial`), availability.
> **Important:** Never run full-library hash automatically; only on explicit user action or `hash_mode='full'` scan option."

---

### Phase 8: Basic PyQt6 GUI — Device Panel, Extractions & Highlights

> **Prompt for Cursor:**
> "Create `src/gui/main_window.py`, `src/gui/device_panel.py`, `src/gui/detail_panel.py`, and wire up `src/main.py`.
>
> 1. **Layout:** splitter with device/root panel (left), extraction/file table (center), detail panel (right).
> 2. **Device panel:** list all `StorageDevice` entries with online/offline indicator, file count, last seen; list `LibraryRoot` under each device.
> 3. **Toolbar:** `Add Library Root`, `Scan Selected Root`, `Scan All`, `Review Name Matches`, `Online Only` filter, search box.
> 4. **Extraction table** (`QTableView` + custom model): columns — `[Original Name]`, Device, Root, Path, Files, Size, **Match Status**, Availability.
> 5. **Row highlighting:** 🟡 exact name match, 🟠 similar name match, 🟢 hash confirmed, default = no highlight.
> 6. **Detail panel:** editable `source_url`, `tags`, `notes`; linked RAR archive info; list of matched folders in same `NameMatchGroup`.
> 7. Apply a clean dark theme (Fusion style or `qdarktheme` if added to requirements).
> 8. On startup, call `refresh_all_device_status` and load catalog + pending name matches count in status bar."

---

### Phase 9: Name Match Review Dialog & Hash Trigger

> **Prompt for Cursor:**
> "Create `src/gui/name_match_dialog.py`.
>
> 1. Open from toolbar or automatically after scan when new matches found.
> 2. List pending `NameMatchGroup` rows grouped by match type (`exact` / `similar`) with similarity score.
> 3. For each group, show all `[Original Name]` folders side-by-side: device, path, file count, total size, availability.
> 4. User actions per group:
>    - **Dismiss** — not a duplicate concern (`review_status=dismissed`).
>    - **Different item** — similar name but intentionally separate (`confirmed_different`).
>    - **Verify with Hash** — run `duplicate_finder.verify_name_match_group` on background thread with progress bar.
> 5. After hash: show ✅ confirmed identical or ❌ mismatch (same name, different content).
> 6. On confirmed: offer open in Explorer, set primary, optional delete (online only)."

---

### Phase 10: GUI Threading & Scan Integration

> **Prompt for Cursor:**
> "Connect scan and hash verification to background threads.
>
> 1. `Add Library Root` → `QFileDialog` → create/select device + insert `LibraryRoot`.
> 2. `Scan Selected Root` / `Scan All` → run `ingestion.py` with `hash_mode='never'` on `QThread`.
> 3. Show `QProgressBar` and status label; badge count for pending name matches.
> 4. Collapsible log pane for match warnings (exact/similar found, offline roots skipped).
> 5. Hash verification runs on separate thread — disable only hash button while running, allow browsing catalog.
> 6. Refresh table model on scan complete; flash/highlight new rows with matches."

---

### Phase 11: File Drill-Down (Files Inside Extraction Folder)

> **Prompt for Cursor:**
> "Extend the GUI to drill into an `ExtractionFolder` row and show individual files inside.
>
> 1. Double-click or expand an extraction row → nested file table.
> 2. File table columns: Name, Size, Type, Relative Path, Availability, Hash (empty until verified).
> 3. Breadcrumb: `Local SSD > Downloads > [Cool Video]`.
> 4. File-level hash still opt-in — only populated after Tier 2 verification."

---

### Phase 12: Explorer, Relink & Offline UX

> **Prompt for Cursor:**
> "Add context menu and offline-aware actions to the extraction and file tables.
>
> 1. **Show in Explorer** — only enabled when `availability == online`; use `file_ops.show_in_explorer`.
> 2. **Rename/Move Folder** — dialog for new path; update `ExtractionFolder` paths; disabled when offline.
> 3. **Relink Library Root** — when device offline or drive letter changed, let user pick new path and call `device_manager.relink_root`.
> 4. **Mark as Missing / Remove from Catalog** — for folders/files deleted on disk.
> 5. Grey out offline/missing rows; tooltip explains why actions are disabled.
> 6. Status bar summary: `3 devices online, 1 offline — 842 extractions (12 pending name matches)`."

---

### Phase 13: Hash-Confirmed Duplicate Review Dialog

> **Prompt for Cursor:**
> "Create `src/gui/duplicate_dialog.py` for **Tier 2 confirmed** duplicates only.
>
> 1. Open from menu: `Tools → Review Hash-Confirmed Duplicates`.
> 2. List groups from `duplicate_finder.find_hash_duplicate_groups`.
> 3. For each group, show side-by-side: device, path, size, availability, linked `NameMatchGroup` original name.
> 4. Let user set **primary** (keeper) copy; optional: open in Explorer, delete non-primary (with confirmation, online only).
> 5. Option to **merge metadata** from duplicates into primary record.
> 6. Mark group as `reviewed` in DB."

---

### Phase 14: Incremental Scan & Startup Refresh

> **Prompt for Cursor:**
> "Enhance ingestion and startup behavior.
>
> 1. On app startup: `refresh_all_device_status`, then optional background light scan (folder names + mtime/size only) for online roots.
> 2. Implement `light_scan_root` vs `full_hash_scan_root` — full hash only when user requests.
> 3. Persist last scan timestamp per root; show in device panel.
> 4. Optional: `QFileSystemWatcher` on local extract directories to detect new `[Original Name]` folders after RAR extract.
> 5. Add menu: `Scan Options → Light (default) / Full Hash`."

---

### Phase 15: Metadata Extraction (Optional Enhancement)

> **Prompt for Cursor:**
> "Create `src/core/metadata.py` for automatic metadata enrichment during ingest.
>
> 1. Images: extract EXIF date, dimensions via Pillow (`DateTimeOriginal`, etc.).
> 2. Videos: optional `pymediainfo` or ffprobe subprocess for duration/resolution/codec.
> 3. Populate `Metadata.download_date` from EXIF if user hasn't set it.
> 4. Store extracted fields in `Metadata.custom_fields` JSON.
> Skip gracefully if libraries/binary missing or file is on offline device."

---

### Phase 17: New Item Reorganize — Flatten, Rename & `[Original Details]`

> **Prompt for Cursor:**
> "Create `src/core/reorganize.py` and `src/gui/reorganize_dialog.py`.
>
> 1. `build_reorganize_plan(extraction_id, new_folder_name, db) -> ReorganizePlan` — walk extraction folder, assign sequence numbers per section 3.14, compute hashes, generate target filenames from config template.
> 2. `capture_original_details(file_path, seq, extraction_root) -> dict` — build `[Original Details]` JSON before any move.
> 3. `preview_reorganize(plan) -> list[Row]` — old relative path, original filename, new filename, sequence, hash8.
> 4. `execute_reorganize(plan, db, progress_callback)` — only after user confirms preview:
>    - Save `original_details` to `Metadata` for each file.
>    - Move all files to `[New Folder Name]/` root with new filenames.
>    - Rename folder `[Original Name]` → `[New Folder Name]` if needed.
>    - Delete empty subfolders; update `Media`/`ExtractionFolder` paths; set `reorganize_status=completed`.
>    - Log `DownloadHistory` event `reorganized`.
> 5. `suggest_new_folder_name(extraction_id, db) -> str` — per section 3.13 priority order.
> 6. GUI dialog: New Folder Name input + suggestion, preview table, Confirm/Cancel; run on background thread.
> 7. Block execution if device offline or `reorganize_status=completed` unless user forces.
> 8. Validate filename length against `max_filename_length`; truncate `{new_folder_name}` segment if needed."

---

### Phase 16: Export, Backup & Packaging (Optional)

> **Prompt for Cursor:**
> "Add export and packaging support.
>
> 1. Export catalog to CSV/JSON (all metadata, works even when NAS offline).
> 2. Optional bulk sidecar export for selected roots (local drives only).
> 3. Add PyInstaller spec for single-file Windows `.exe`; document build steps in README.
> 4. Ensure `catalog.db` path defaults to user AppData, not project directory."

---

## 6. UI Reference Layout

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ [Add Root] [Scan All] [Review Name Matches (3)]  [Online Only ☑]  🔍 Search  │
├──────────────┬───────────────────────────────────────┬───────────────────────┤
│ Devices      │  Extraction Folders                   │  Detail Panel         │
│ 🟢 Local SSD │  🟡 [Cool Video]  Local SSD  12 files │  Original: Cool Video │
│   └ Downloads│  🟠 [Cool Video!] NAS         10 files│  Matches: 2 pending   │
│ 🟢 Local HDD │      [New Item]   Local HDD    8 files│  [Verify with Hash]   │
│ 🔴 Synology  │                                       │  [Dismiss] [Different]│
├──────────────┴───────────────────────────────────────┴───────────────────────┤
│ Light scan: 45/120...  │  🟡 Exact: 1  🟠 Similar: 2  │  Offline: 1 device │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 7. Suggested Build Order Summary

| Order | Phase | Deliverable |
|-------|-------|-------------|
| 1 | Phase 1 | Multi-device SQLite schema + extraction/name-match tables |
| 2 | Phase 2 | Device online/offline + relink |
| 3 | Phase 3–4 | Scanner + file ops |
| 4 | Phase 5–6 | Name matcher (Tier 1) + light ingestion |
| 5 | Phase 7 | Hash verification on demand (Tier 2) |
| 6 | Phase 8–10 | GUI + name match dialog + threading |
| 7 | Phase 11–13 | File drill-down + offline UX + hash-confirmed dialog |
| 8 | Phase 14 | Watch folder after RAR extract |
| 9 | Phase 15–17 | Metadata extraction + export + reorganize (optional) |

## 8. Requirements Notes

Update `requirements.txt` as phases progress:

```text
PyQt6
Pillow
rapidfuzz
# Phase 2 optional: pywin32 (volume serial detection)
# Phase 15 optional: pymediainfo
# Phase 16 optional: pyinstaller
```

Remove `pathlib` from requirements — it is Python stdlib. Defer `numpy` / `pandas` until analytics features are needed.
