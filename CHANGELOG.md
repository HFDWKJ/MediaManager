# Changelog

All notable changes to Media Manager are documented here.

## 0.0.4 — 2026-06-01

Developer: **Dong, Zhexi**

### Added
- **Multilingual README** — documentation in English, 简体中文, 日本語, Français, Deutsch, 한국어, and Español with a shared language switcher
- **Cursor & Vibe Coding** project documentation on the GitHub homepage
- Optional `update.github_token` config and `GITHUB_TOKEN` / `MEDIA_MANAGER_GITHUB_TOKEN` env support for private-repo updates

### Changed
- App icon refreshed with a **transparent background** and modern flat design (PNG + ICO)
- README layout redesigned with centered logo, badges, and table of contents (manim-style)

### Fixed
- **In-app update** now detects Nuitka compiled builds via `utils.runtime.is_compiled()` instead of relying only on `sys.frozen`
- Packaged apps download and install updates in-app instead of opening the browser when an update is available
- GitHub update check shows a clear error when a private repository is inaccessible without a token
- Application root, window icon, and changelog paths use `is_compiled()` for Nuitka standalone runs

## 0.0.3 — 2026-06-01

Developer: **Dong, Zhexi**

### Added
- Application icon (`assets/media_manager_app_icon.png` + `.ico`) embedded in source and packaged builds
- Reorganize dialog graphical progress bar with percentage, ETA, and current filename
- PyQt6 step-by-step installer (Nuitka onefile setup; no Inno Setup)

### Packaging
- `MediaManagerSetup_0.0.3.exe` — installed edition
- `MediaManagerPortal_v0.0.3.zip` — portable edition

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
