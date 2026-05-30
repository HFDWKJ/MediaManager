# Media Manager — Development Roadmap

Track releases and milestones on GitHub:

- [Milestone v0.0.3](https://github.com/HFDWKJ/MediaManager/milestone/1)
- [All open v0.0.3 issues](https://github.com/HFDWKJ/MediaManager/issues?q=is%3Aissue+is%3Aopen+milestone%3Av0.0.3)

Developer: **Dong, Zhexi**

---

## v0.0.3 — Stability & core workflow closure

**Target theme:** Fix packaging UX, close gaps in the duplicate/RAR workflow, and make multi-device catalogs easier to maintain.

**Packaging rule:** Nuitka only (no Inno Setup). Installer = PyQt6 wizard + Nuitka onefile setup exe (`--include-raw-dir`).

### P0 — Must ship

| ID | Task | Issue | Area |
|----|------|-------|------|
| 0.3-01 | **PyQt6 step-by-step installer** — Welcome → install path → options (desktop shortcut) → progress → finish; keep `/VERYSILENT` for in-app updates | [#1](https://github.com/HFDWKJ/MediaManager/issues/1) | installer |
| 0.3-02 | **Installer regression tests** — script or checklist: silent install, launch app, uninstall; verify `include-raw-dir` payload | [#2](https://github.com/HFDWKJ/MediaManager/issues/2) | build / QA |
| 0.3-03 | **Library root path relink** — when drive letter or NAS path changes, UI to map old root → new path and refresh catalog availability | [#3](https://github.com/HFDWKJ/MediaManager/issues/3) | core / gui |
| 0.3-04 | **Duplicate review UI** — after hash verify: list `DuplicateGroup`, pick keeper, mark copies (integrate with Name Matches flow) | [#4](https://github.com/HFDWKJ/MediaManager/issues/4) | gui / core |
| 0.3-05 | **RAR → extraction linking** — `archive_tracker`: associate `.rar` with `[Original Name]` folder; suggest `[New Folder Name]` from archive filename | [#5](https://github.com/HFDWKJ/MediaManager/issues/5) | core |

### P1 — Should ship

| ID | Task | Issue | Area |
|----|------|-------|------|
| 0.3-06 | **Settings: scan & match** — expose `similarity_threshold`, skip extensions, hash-on-scan default in Settings dialog | [#6](https://github.com/HFDWKJ/MediaManager/issues/6) | gui / config |
| 0.3-07 | **Settings: reorganize** — expose filename template, filetype prefixes (IMG/VID/NIV), delete-empty-subfolders in Settings | [#7](https://github.com/HFDWKJ/MediaManager/issues/7) | gui / config |
| 0.3-08 | **Catalog search & filter** — text search on folder name/path; filter by device type, match status, reorganize status | [#8](https://github.com/HFDWKJ/MediaManager/issues/8) | gui |
| 0.3-09 | **Catalog table sort** — click column headers to sort; remember last sort in session | [#9](https://github.com/HFDWKJ/MediaManager/issues/9) | gui |
| 0.3-10 | **Batch delete extractions** — multi-select rows in catalog table, confirm, delete | [#10](https://github.com/HFDWKJ/MediaManager/issues/10) | gui |

### P2 — Nice to have (v0.0.3 or defer to v0.1.0)

| ID | Task | Issue | Area |
|----|------|-------|------|
| 0.3-11 | **Operation log panel** — read-only view of `DownloadHistory` (import, reorganize, relink events) | [#11](https://github.com/HFDWKJ/MediaManager/issues/11) | gui |
| 0.3-12 | **GitHub Actions CI** — build Nuitka standalone on push/tag; optional attach artifacts to Release | [#12](https://github.com/HFDWKJ/MediaManager/issues/12) | devops |
| 0.3-13 | **pytest smoke tests** — database CRUD, name normalization, version compare (update_checker) | [#13](https://github.com/HFDWKJ/MediaManager/issues/13) | tests |

### Definition of done (v0.0.3)

- [ ] All **P0** issues closed ([#1](https://github.com/HFDWKJ/MediaManager/issues/1)–[#5](https://github.com/HFDWKJ/MediaManager/issues/5))
- [ ] `MediaManagerSetup_0.0.3.exe` and `MediaManagerPortal_v0.0.3.zip` built with Nuitka and uploaded to [Release v0.0.3](https://github.com/HFDWKJ/MediaManager/releases)
- [ ] `CHANGELOG.md` updated; About dialog shows 0.0.3 notes
- [ ] Silent update path tested: 0.0.2 → 0.0.3 (installed + portable)
- [ ] No open **P0** issues on milestone v0.0.3

### Suggested implementation order

```text
Phase 1   #1, #2     PyQt6 installer wizard + install QA
Phase 2   #3, #4     Path relink + duplicate review UI
Phase 3   #5, #6, #7 RAR tracker + settings panels
Phase 4   #8–#10     Catalog UX (search, sort, batch delete)
Phase 5   #11–#13    Log panel, CI, pytest (as time allows)
Release   Tag v0.0.3, publish installers on GitHub Releases
```

---

## v0.1.0 — Performance & metadata (planned)

| Task | Notes |
|------|-------|
| Parallel scan workers | Configurable local vs network worker counts |
| EXIF / basic media info | Pillow: dimensions, duration where available |
| Sidecar JSON export | Optional write beside files on NAS |
| Batch reorganize | Queue multiple extractions |

---

## v0.2.0 — Polish (planned)

| Task | Notes |
|------|-------|
| Thumbnail preview | Selected image/video in detail panel |
| Advanced duplicate actions | Open both folders, export duplicate report |
| i18n groundwork | English first; structure for future locales |

---

## How to use this doc

1. Pick an issue from the [v0.0.3 milestone](https://github.com/HFDWKJ/MediaManager/milestone/1).
2. Branch: `feature/0.3-xx-short-name` (example: `feature/0.3-01-installer-wizard`).
3. Commit message: `feat(installer): PyQt6 wizard (#1)`.
4. Open a PR referencing the issue; close via `Closes #1` in the PR body.
5. When cutting the release, check off **Definition of done** above and update `CHANGELOG.md`.
