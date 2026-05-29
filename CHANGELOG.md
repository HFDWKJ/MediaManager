# Changelog

All notable changes to Media Manager are documented here.

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
