# Windows installation and antivirus notes

## Recommended installer (v0.0.4.1+)

The **folder installer** reduces false positives compared to the old single-file setup:

1. Download `MediaManagerSetup_0.0.4.1.zip` from [GitHub Releases](https://github.com/HFDWKJ/MediaManager/releases).
2. Right-click the zip → **Extract All…**
3. Open the extracted folder and run **`MediaManagerSetup_0.0.4.1.exe`**
4. Do **not** run only the zip file itself.

The folder contains:

- `MediaManagerSetup_*.exe` — small setup program (no self-extracting blob)
- `payload\` — application files copied during install

## If Windows blocks the file

This project is **not malware**. Unsigned Nuitka builds are often flagged as “potentially unwanted software”.

- **Windows Security** → **Protection history** → **Allow** / **Restore**
- Add an exclusion for `%LOCALAPPDATA%\MediaManager` or your download folder
- Submit a false positive: [Microsoft file submission](https://www.microsoft.com/en-us/wdsi/filesubmission)
- **Portable edition**: `MediaManagerPortal_v*.zip` (no setup exe)
- **Production**: sign executables with an Authenticode certificate

## Packaging options (this project)

| Method | Used here | Notes |
|--------|-----------|--------|
| **Nuitka standalone folder installer** | Yes (default) | Lower false-positive rate than onefile |
| **Nuitka onefile installer** | Optional (`-InstallerMode onefile`) | Often blocked by Defender |
| **Nuitka portable zip** | Yes | Extract and run `MediaManager.exe` |
| Inno Setup / MSI | No | Not used per project policy |
| PyInstaller | Legacy | Replaced by Nuitka |
