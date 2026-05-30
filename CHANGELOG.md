# Changelog

All notable changes to Media Manager are documented here.

## Unreleased — v0.0.3 (in progress)

See [docs/ROADMAP.md](docs/ROADMAP.md) and [GitHub milestone v0.0.3](https://github.com/HFDWKJ/MediaManager/milestone/1).

### Planned
- PyQt6 step-by-step installer (Nuitka; no Inno Setup)
- Installer build/regression checks
- Library root path relink when drives or NAS paths change
- Duplicate review UI after hash verification
- RAR → extraction folder linking (`archive_tracker`)
- Settings UI for scan, name match, and reorganize options
- Catalog search, sort, and batch delete

## 0.0.2 — 2026-05-29

Developer: **Dong, Zhexi**

### Added
- **Automatic update check on startup** — after launch, checks GitHub for a newer release; prompts to download and update or choose **Later** (same version is not prompted again until a newer release appears)
- **Options → Check for updates…** — manual check; download and apply the latest installer (installed edition) or portable zip (portal edition)
- **Settings → Updates** — toggle **Check for updates when the application starts**
- Updates are fetched from [GitHub Releases](https://github.com/HFDWKJ/MediaManager/releases) (`MediaManagerSetup_*.exe` Nuitka installer or `MediaManagerPortal_v*.zip`)

### Notes
- Running from source opens the releases page in the browser instead of in-app install
- Publish a GitHub release with matching asset names for updates to be offered

## 0.0.1 — 2026-05-29

Developer: **Dong, Zhexi**

### Added
- **Portable (portal) edition** — `data\` folder beside the app for config, database, and logs (no `%APPDATA%`)
- **Options → About…** — version info, developer credit, and in-app changelog
- Face UID manager — search across all fields and sort by column headers
- Export database / Import database (Tools menu) for backup and cross-device sync

### Changed
- Reorganize filename prefixes: **IMG** (image), **VID** (video), **NIV** (other)
- Packaging switched to **Nuitka** with Inno Setup installer

### Fixed
- Face UID Nick Name duplicate prompt and form handling
- Installer build path detection for packaged output

## 0.0.0 — 2026-05-29

Initial test release.

### Catalog & library
- DiskGenius-style dark/light UI with library tree by device type (SSD, HDD, NAS, DAS)
- Add library roots and catalog extraction folders
- Database table with folder details, reorganization, and name matching
- Reorganize workflow with marker files and CSV reports

### Tools
- Face UID manager — unique 5-character IDs with Nick Name, Region, and Comments
- Nick Name duplicate detection with option to continue adding

### Packaging
- First Nuitka standalone build and Windows installer (Inno Setup)
