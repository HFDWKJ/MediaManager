<p align="center">
  <img src="assets/media_manager_app_icon.png" alt="Media Manager" width="128"/>
</p>

<h1 align="center">Media Manager</h1>

<p align="center">
  <strong>English</strong> · <a href="README.zh-CN.md">简体中文</a>
</p>

<p align="center">
  <a href="https://github.com/HFDWKJ/MediaManager/releases"><img src="https://img.shields.io/github/v/release/HFDWKJ/MediaManager?label=release&logo=github" alt="Release"/></a>
  <a href="https://github.com/HFDWKJ/MediaManager"><img src="https://img.shields.io/badge/platform-Windows-0078D6?logo=windows" alt="Windows"/></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white" alt="Python"/></a>
  <a href="https://www.riverbankcomputing.com/software/pyqt/"><img src="https://img.shields.io/badge/GUI-PyQt6-41CD52?logo=qt" alt="PyQt6"/></a>
</p>

<p align="center">
  Windows desktop app to catalog media across multiple drives and devices,<br/>
  detect <code>[Original Name]</code> folder duplicates, and reorganize extracted downloads.
</p>

<p align="center">
  <b>Version:</b> 0.0.3 · <b>Developer:</b> Dong, Zhexi
</p>

---

## Table of contents

- [Features](#features)
- [Download](#download)
- [Quick start](#quick-start)
- [Built with Cursor & Vibe Coding](#built-with-cursor--vibe-coding)
- [Build (Nuitka)](#build-nuitka-only)
- [Config & data paths](#config--data-paths)
- [Application updates](#application-updates)
- [Project structure](#project-structure)
- [Roadmap & docs](#roadmap--docs)
- [License](#license)

---

## Features

| Area | Description |
|------|-------------|
| **Multi-root library** | Index folders on SSD/HDD, NAS, DAS, and USB; catalog stays usable when a device is offline |
| **Duplicate detection** | Tier 1: fast `[Original Name]` fuzzy match · Tier 2: SHA-256 when you choose **Verify with Hash** |
| **Reorganize** | Flatten extraction folders into `[Collections]` with templates, progress bar, percentage, and ETA |
| **Face UID** | Short unique IDs with nicknames, region, and comments |
| **Portable edition** | `data\` beside the exe for config, database, and logs |
| **Auto-update** | Checks [GitHub Releases](https://github.com/HFDWKJ/MediaManager/releases) on startup |
| **UI** | DiskGenius-inspired dark theme and Office-style ribbon |

---

## Download

Pre-built binaries are published on **[GitHub Releases](https://github.com/HFDWKJ/MediaManager/releases)**:

| Edition | File |
|---------|------|
| Installer | `MediaManagerSetup_0.0.3.exe` |
| Portable zip | `MediaManagerPortal_v0.0.3.zip` |

> [!NOTE]
> **Smart App Control:** Unsigned builds may be blocked on Windows 11. Turn off SAC on a test machine, or sign the installer for production use.

---

## Quick start

### Requirements

- Python 3.10+
- Windows 11 (Windows 10+ supported)

### Setup & run

```powershell
git clone https://github.com/HFDWKJ/MediaManager.git
cd MediaManager
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\create_test_data.py   # optional sample folders
python src\main.py
```

### Try the workflow

1. **Add Library Root** — point at `test_data\library` or your download folder.
2. **Discover / Scan** — index `[Original Name]` extraction folders.
3. **Review Name Matches** — dismiss, mark different, or **Verify with Hash**.
4. **Reorganize ([Collections])** — preview flatten/rename.
5. **Show in Explorer** — open the folder when the device is online.

> [!TIP]
> Running from source opens the GitHub releases page when you choose **Download and update**. Packaged builds download and install in-app.

---

## Built with Cursor & Vibe Coding

This project is a **real-world test of AI-assisted development** with [Cursor](https://cursor.com) and **Vibe Coding**: describe intent in natural language, let the Agent implement, then refine by running the app and giving feedback.

| Stage | How |
|-------|-----|
| **Planning** | [`media_manager_plan.md`](media_manager_plan.md) — phased prompts for each milestone |
| **Implementation** | Agent built `core/`, `gui/`, packaging scripts, and release flow step by step |
| **UI iteration** | Screenshot-driven feedback (ribbon, progress bar, filters) |
| **Release tracking** | [`docs/ROADMAP.md`](docs/ROADMAP.md) + GitHub Issues / Milestones |

**Typical loop:** Prompt → Agent edits → run `MediaManager.exe` → screenshot / error feedback → ship release.

> Chinese documentation for this section: **[README.zh-CN.md § Cursor 开发](README.zh-CN.md#使用-cursor-与-vibe-coding-开发)**

### Practical notes

- Keep a living plan (`media_manager_plan.md`) for stable Agent context across sessions.
- Test **packaged** Nuitka builds early — runtime detection differs from `python src\main.py`.
- Packaging rule: **Nuitka only**, no Inno Setup (enforced via Cursor user rules).
- Public GitHub Releases simplify auto-update (no token required).

---

## Build (Nuitka only)

Build scripts install dependencies automatically. Nuitka uses MSVC when available, otherwise MinGW64.

### Application

```powershell
.\scripts\build_nuitka.ps1              # dist\MediaManager\MediaManager.exe
.\scripts\build_nuitka.ps1 -Mode onefile  # dist\MediaManager.exe
```

### Installer

```powershell
.\scripts\build_installer.ps1
# → dist_installer\MediaManagerSetup_0.0.3.exe
```

Silent flags for in-app updates: `/VERYSILENT`, `/SUPPRESSMSGBOXES`, `/NORESTART`, `/CLOSEAPPLICATIONS`, optional `/DIR=...`.

### Portable zip

```powershell
.\scripts\build_portal.ps1
# → dist_portal\MediaManagerPortal_v0.0.3.zip
```

---

## Config & data paths

**Installed edition**

| Item | Path |
|------|------|
| Config | `%APPDATA%\MediaManager\config.json` |
| Database | `%APPDATA%\MediaManager\catalog.db` |
| Logs | `%APPDATA%\MediaManager\logs\` |

**Portable edition** — `portable.marker` beside `MediaManager.exe`, or use the portal build:

| Item | Path |
|------|------|
| Config | `data\config.json` |
| Database | `data\catalog.db` |
| Logs | `data\logs\` |

Copy the **entire folder** (including `data\`) to move catalog and settings to another PC.

---

## Application updates

- **Startup check** (on by default) and **Options → Check for updates…**
- Disable in **Settings → Updates**
- Tag releases `v0.0.3`; release notes appear in the update dialog
- Private repos: set `update.github_token` in config or `GITHUB_TOKEN` env var

---

## Project structure

```text
src/
  main.py              Entry point
  core/                Database, scan, match, reorganize, updates
  gui/                 PyQt6 UI
  installer/           Nuitka setup wizard
  utils/               Config, logging, paths
assets/                App icon
scripts/               Build & helper scripts
docs/ROADMAP.md        Milestone checklist
media_manager_plan.md  Cursor phased development plan
CHANGELOG.md           Release notes (shown in About dialog)
```

---

## Roadmap & docs

| Document | Description |
|----------|-------------|
| [README.zh-CN.md](README.zh-CN.md) | 简体中文文档 |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Version plans and v0.0.3 checklist |
| [CHANGELOG.md](CHANGELOG.md) | Release history |
| [GitHub Milestones](https://github.com/HFDWKJ/MediaManager/milestones) | Issue tracking |
| [media_manager_plan.md](media_manager_plan.md) | Full Cursor development plan |

---

## License

Private / personal project by **Dong, Zhexi**. See repository settings for distribution terms.
