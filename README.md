# Media Manager

Windows desktop app to catalog media across multiple drives, detect `[Original Name]` folder duplicates, and reorganize new extractions.

## Requirements

- Python 3.10+
- Windows 11 (tested on Windows 10+)

## Setup

```powershell
cd c:\_Workspace\DevPlan
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Create test data

```powershell
python scripts\create_test_data.py
```

This creates `test_data\library\` with sample `[Cool Video]` folders.

## Run the app

```powershell
python src\main.py
```

## Build an .exe (Nuitka)

Build dependencies are installed by the script. On Windows, Nuitka uses MSVC if available, otherwise MinGW64.

```powershell
.\scripts\build_nuitka.ps1
```

Output:

- `dist\MediaManager\MediaManager.exe` (standalone folder, recommended)

Optional single-file build:

```powershell
.\scripts\build_nuitka.ps1 -Mode onefile
```

- `dist\MediaManager.exe`

Legacy alias:

```powershell
.\scripts\build_exe.ps1
```

## Windows installer (Nuitka)

Build the standalone app and a single-file setup executable (no Inno Setup):

```powershell
.\scripts\build_installer.ps1
```

Output:

- `dist_installer\MediaManagerSetup_0.0.2.exe` (version follows `src/version.py`)

The installer will:

- Install into `C:\Program Files\Media Manager` by default (folder picker when run interactively).
- Create a Start Menu shortcut.
- Register an uninstaller in **Apps & features** (`Uninstall.exe` in the install folder).

Silent flags (used by in-app updates): `/VERYSILENT`, `/SUPPRESSMSGBOXES`, `/NORESTART`, `/CLOSEAPPLICATIONS`, optional `/DIR=...`.

## Quick test workflow

1. **Add Library Root** — select `test_data\library` (or your real download folder).
2. **Select Extraction Folder** — open Windows Explorer to pick or create one folder (inside a library root).
3. **Scan All** — indexes all subfolders under a library root; highlights exact/similar matches.
4. **Review Name Matches** — dismiss, mark different, or **Verify with Hash**.
5. Select a folder → **Reorganize ([Collections])** — preview flatten/rename with `[New Folder Name]`.
6. **Show in Explorer** — open selected folder in Windows Explorer.

## Config & database

**Installed edition** (default):

- Config: `%APPDATA%\MediaManager\config.json`
- Catalog DB: `%APPDATA%\MediaManager\catalog.db`
- Logs: `%APPDATA%\MediaManager\logs\media_manager.log`

**Portable (portal) edition** — no installer; all data next to the app:

- Put `portable.marker` beside `MediaManager.exe`, or build with the portal script (creates it automatically).
- Config / DB / logs: `data\config.json`, `data\catalog.db`, `data\logs\`
- Copy the **whole folder** (including `data\`) to another PC to keep catalog and settings together.

Build portable zip:

```powershell
.\scripts\build_portal.ps1
```

Output:

- `dist_portal\MediaManager\` — run `MediaManager.exe` directly
- `dist_portal\MediaManagerPortal_v0.0.1.zip` — distribute this

Dev portable mode: create an empty `portable.marker` in the repo root and run `python src\main.py` — data goes to `data\`.

## GitHub (track source changes)

Only **source code** is tracked — not `data\`, build output (`dist\`), or your personal `catalog.db`.

1. Install [Git for Windows](https://git-scm.com/download/win) and [GitHub CLI](https://cli.github.com/) (optional but recommended).
2. Log in: `gh auth login`
3. Push from project root:

```powershell
.\scripts\push_to_github.ps1 -RepoName MediaManager
```

Or if you already created an empty repo on GitHub:

```powershell
.\scripts\push_to_github.ps1 -RepoUrl https://github.com/YOUR_USER/MediaManager.git
```

Day-to-day:

```powershell
git add .
git commit -m "Describe your change"
git push
```

Release builds (installer / portal zip) stay in `dist_installer\` and `dist_portal\` — upload those manually to [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github) if you want to distribute binaries.

## Project structure

```text
src/
  main.py           Entry point
  core/             Database, scan, name match, reorganize
  gui/              PyQt6 UI
  utils/            Config, logging
scripts/
  create_test_data.py
```

See `media_manager_plan.md` for the full development plan.

## Roadmap & tracking

- **[docs/ROADMAP.md](docs/ROADMAP.md)** — version plans and v0.0.3 task checklist
- **[GitHub Issues / Milestones](https://github.com/HFDWKJ/MediaManager/milestones)** — development tracking

## Application updates (v0.0.2+)

The app checks [GitHub Releases](https://github.com/HFDWKJ/MediaManager/releases) for newer versions.

- **On startup** (optional, default on): prompts when a newer release is available.
- **Options → Check for updates…**: manual check and install.
- **Settings**: disable startup checks under **Updates**.

Publish a release with assets named like the build outputs:

| Edition | Asset name |
|---------|------------|
| Installer (Nuitka setup exe) | `MediaManagerSetup_0.0.2.exe` |
| Portable | `MediaManagerPortal_v0.0.2.zip` |

Tag the release `v0.0.2` (or `0.0.2`). Release notes in the GitHub release body appear in the update dialog.

## Changelog

Release notes live in `CHANGELOG.md` at the project root. They appear in **Options → About…** inside the app. Add a new `## version — date` section for each release.
