# Media Manager

**Version:** 0.0.3 · **Developer:** Dong, Zhexi · **Platform:** Windows 11 (Windows 10+)

A Windows desktop app to catalog media across multiple drives and devices, detect `[Original Name]` folder duplicates, and reorganize extracted downloads — without moving files off NAS or offline volumes by default.

**Repository:** [github.com/HFDWKJ/MediaManager](https://github.com/HFDWKJ/MediaManager)

---

## Features

- **Multi-root library** — index folders on local SSD/HDD, NAS, DAS, and USB; catalog stays usable when a device is offline
- **Two-tier duplicate detection** — fast `[Original Name]` fuzzy match first; SHA-256 hash only when you choose **Verify with Hash**
- **Reorganize workflow** — flatten extraction folders into `[Collections]` with configurable rename templates and progress UI
- **Face UID manager** — short unique IDs with nicknames, region, and comments
- **Portable edition** — `data\` beside the exe for config, database, and logs
- **Auto-update** — checks [GitHub Releases](https://github.com/HFDWKJ/MediaManager/releases) on startup; in-app download and silent install for packaged builds
- **DiskGenius-inspired UI** — dark theme, Office-style ribbon, library tree grouped by device type

---

## Built with Cursor & Vibe Coding

This project is a **real-world test of AI-assisted development** using [Cursor](https://cursor.com) and its **Vibe Coding** workflow: describe intent in natural language, let the agent implement and iterate, and refine through running the app and giving feedback.

### What we tested

| Area | Approach |
|------|----------|
| **Planning** | [`media_manager_plan.md`](media_manager_plan.md) — phased technical spec with copy-paste prompts for each milestone |
| **Implementation** | Cursor Agent built core logic (`core/`), PyQt6 UI (`gui/`), packaging scripts, and GitHub release flow step by step |
| **UI iteration** | Screenshot-driven feedback (e.g. Office ribbon, toolbar layout, reorganize progress bar) instead of hand-writing every widget |
| **Debugging** | Agent reads logs, reproduces build failures (Nuitka vs PyInstaller, installer payload paths), and patches in-repo |
| **Release tracking** | Roadmap in [`docs/ROADMAP.md`](docs/ROADMAP.md), GitHub Issues/Milestones, and CHANGELOG kept in sync with Agent help |

### Typical Vibe Coding loop

1. **Prompt** — paste a phase from `media_manager_plan.md`, or describe a bug/feature in chat (Chinese or English both work).
2. **Agent edits** — Cursor modifies source, scripts, and docs; runs imports/builds when needed.
3. **Run & verify** — `python src\main.py` or the packaged `MediaManager.exe` on a real Windows machine.
4. **Feedback** — share screenshots, expected behavior, or error text; Agent adjusts UI and logic.
5. **Ship** — bump `src/version.py`, update `CHANGELOG.md`, build with Nuitka, upload to GitHub Releases.

### Practical notes from this project

- **Keep a living plan** — `media_manager_plan.md` gives the Agent stable context across long sessions.
- **Prefer small phases** — database → scanner → GUI → packaging reduces bad assumptions.
- **Test packaged builds early** — Nuitka uses `__compiled__`, not only `sys.frozen`; installer and auto-update logic must be validated on compiled exe, not just `python src\main.py`.
- **User rules help** — e.g. “Nuitka only, no Inno Setup” persists across chats via Cursor rules.
- **Public releases simplify updates** — GitHub Releases API works without a token when the repo is public.

### 中文摘要 · 使用 Cursor 与 Vibe Coding 开发

本项目全程在 **Cursor** 中用 **Vibe Coding**（自然语言驱动 + Agent 写代码 + 人工验收）方式迭代：

- **需求与分阶段计划** 写在 [`media_manager_plan.md`](media_manager_plan.md)，按 Phase 逐步交给 Agent 实现。
- **界面与交互** 通过截图反馈快速调整（Ribbon、进度条、筛选栏等），无需从零手写全部 UI。
- **打包与发布** 同样由 Agent 维护脚本（Nuitka 独立目录、安装包、便携版 zip、自动更新）。
- **协作方式**：中文或英文描述问题均可；运行 exe 验证后把现象或截图发回，Agent 继续改代码。

适合作为「个人工具 + AI 结对编程」的参考样本：计划文档 + 里程碑 + 可运行交付物，而不是一次性生成的 demo。

---

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

Creates `test_data\library\` with sample `[Cool Video]` folders.

## Run the app

```powershell
python src\main.py
```

Running from source opens the GitHub releases page in the browser when you choose **Download and update**. Packaged builds use in-app download and silent install.

---

## Build (Nuitka only)

**Packaging rule:** Nuitka only — no Inno Setup. Build dependencies are installed by the scripts. On Windows, Nuitka uses MSVC when available, otherwise MinGW64.

### Application (standalone folder)

```powershell
.\scripts\build_nuitka.ps1
```

Output: `dist\MediaManager\MediaManager.exe`

Optional single-file build:

```powershell
.\scripts\build_nuitka.ps1 -Mode onefile
```

Output: `dist\MediaManager.exe`

Legacy alias: `.\scripts\build_exe.ps1`

### Windows installer

Builds the app plus a single-file setup executable (PyQt6 wizard + Nuitka onefile, `--include-raw-dir` payload):

```powershell
.\scripts\build_installer.ps1
```

Or directly:

```powershell
.\scripts\build_nuitka_installer.ps1
```

Output: `dist_installer\MediaManagerSetup_0.0.3.exe` (version follows `src/version.py`)

The installer:

- Defaults to `C:\Program Files\Media Manager` (folder picker when run interactively)
- Creates a Start Menu shortcut and registers **Apps & features** uninstall
- Supports silent flags for in-app updates: `/VERYSILENT`, `/SUPPRESSMSGBOXES`, `/NORESTART`, `/CLOSEAPPLICATIONS`, optional `/DIR=...`

### Portable (portal) zip

```powershell
.\scripts\build_portal.ps1
```

Output:

- `dist_portal\MediaManager\` — run `MediaManager.exe` directly
- `dist_portal\MediaManagerPortal_v0.0.3.zip` — distribute this

---

## Quick test workflow

1. **Add Library Root** — select `test_data\library` or your real download folder.
2. **Discover / Scan** — find and index `[Original Name]` extraction folders under roots.
3. **Review Name Matches** — dismiss, mark different, or **Verify with Hash**.
4. Select a folder → **Reorganize ([Collections])** — preview flatten/rename with progress bar, percentage, and ETA.
5. **Show in Explorer** — open the selected folder in Windows Explorer (when online).

---

## Config & database

**Installed edition** (default):

| Item | Path |
|------|------|
| Config | `%APPDATA%\MediaManager\config.json` |
| Catalog DB | `%APPDATA%\MediaManager\catalog.db` |
| Logs | `%APPDATA%\MediaManager\logs\media_manager.log` |

**Portable edition** — put `portable.marker` beside `MediaManager.exe`, or use the portal build script:

| Item | Path |
|------|------|
| Config | `data\config.json` |
| Catalog DB | `data\catalog.db` |
| Logs | `data\logs\` |

Copy the **whole folder** (including `data\`) to move catalog and settings to another PC.

Dev portable mode: create an empty `portable.marker` in the repo root and run `python src\main.py`.

---

## Application updates

The app checks [GitHub Releases](https://github.com/HFDWKJ/MediaManager/releases) for newer versions.

- **On startup** (default on) — prompt when a newer release is available
- **Options → Check for updates…** — manual check and install
- **Settings** — disable startup checks under **Updates**

Publish releases with assets named like the build outputs:

| Edition | Asset name |
|---------|------------|
| Installer | `MediaManagerSetup_0.0.3.exe` |
| Portable | `MediaManagerPortal_v0.0.3.zip` |

Tag releases `v0.0.3` (or `0.0.3`). Release notes in the GitHub release body appear in the update dialog.

For **private** repositories, set `update.github_token` in config or the `GITHUB_TOKEN` environment variable. Public repos do not require a token.

---

## GitHub (source & releases)

Only **source code** is tracked in git — not `data\`, `dist\`, `dist_installer\`, `dist_portal\`, or local `catalog.db`.

```powershell
gh auth login
.\scripts\push_to_github.ps1 -RepoUrl https://github.com/HFDWKJ/MediaManager.git
```

Day-to-day:

```powershell
git add .
git commit -m "Describe your change"
git push
```

Upload `dist_installer\*.exe` and `dist_portal\*.zip` to [GitHub Releases](https://github.com/HFDWKJ/MediaManager/releases) for distribution and auto-update.

---

## Project structure

```text
src/
  main.py                 Entry point
  version.py              Version and developer metadata
  core/                   Database, scan, match, reorganize, updates
  gui/                    PyQt6 UI (ribbon, dialogs, workers)
  installer/              Nuitka-based setup wizard
  utils/                  Config, logging, paths, runtime detection
assets/                   App icon (png + ico)
scripts/                  Build, test data, push helpers
docs/ROADMAP.md           Version plans and milestone checklist
media_manager_plan.md     Cursor phased development plan (prompt library)
CHANGELOG.md              Release notes (shown in About dialog)
```

---

## Roadmap & changelog

- **[docs/ROADMAP.md](docs/ROADMAP.md)** — version plans and v0.0.3 task checklist
- **[GitHub Issues / Milestones](https://github.com/HFDWKJ/MediaManager/milestones)** — development tracking
- **[CHANGELOG.md](CHANGELOG.md)** — release history; add a `## version — date` section for each release

---

## License

Private / personal project by **Dong, Zhexi**. See repository settings for distribution terms.
