<p align="center">
  <img src="assets/media_manager_app_icon.png" alt="Media Manager" width="128"/>
</p>

<h1 align="center">Media Manager</h1>

<p align="center">
  <a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.fr.md">Français</a> · <strong>Deutsch</strong> · <a href="README.ko.md">한국어</a> · <a href="README.es.md">Español</a>
</p>

<p align="center">
  <a href="https://github.com/HFDWKJ/MediaManager/releases"><img src="https://img.shields.io/github/v/release/HFDWKJ/MediaManager?label=release&logo=github" alt="Release"/></a>
  <a href="https://github.com/HFDWKJ/MediaManager"><img src="https://img.shields.io/badge/platform-Windows-0078D6?logo=windows" alt="Windows"/></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white" alt="Python"/></a>
  <a href="https://www.riverbankcomputing.com/software/pyqt/"><img src="https://img.shields.io/badge/GUI-PyQt6-41CD52?logo=qt" alt="PyQt6"/></a>
</p>

<p align="center">
  Windows-Desktop-App zum Katalogisieren von Medien über mehrere Laufwerke und Geräte,<br/>
  Erkennen von <code>[Original Name]</code>-Ordner-Duplikaten und Organisieren entpackter Downloads.
</p>

<p align="center">
  <b>Version:</b> 0.0.4 · <b>Entwickler:</b> Dong, Zhexi
</p>

---

## Inhaltsverzeichnis

- [Funktionen](#funktionen)
- [Download](#download)
- [Schnellstart](#schnellstart)
- [Entwicklung mit Cursor & Vibe Coding](#entwicklung-mit-cursor--vibe-coding)
- [Build (Nuitka)](#build-nuitka)
- [Konfiguration und Datenpfade](#konfiguration-und-datenpfade)
- [Anwendungs-Updates](#anwendungs-updates)
- [Projektstruktur](#projektstruktur)
- [Roadmap & Dokumentation](#roadmap--dokumentation)
- [Lizenz](#lizenz)

---

## Funktionen

| Bereich | Beschreibung |
|---------|--------------|
| **Multi-Root-Bibliothek** | Indizierung auf SSD/HDD, NAS, DAS und USB; Katalog bleibt bei offline Geräten nutzbar |
| **Duplikaterkennung** | Stufe 1: unscharfer `[Original Name]`-Abgleich · Stufe 2: SHA-256 bei **Verify with Hash** |
| **Reorganisieren** | Entpack-Ordner in `[Collections]` abflachen; Vorlagen, Fortschrittsbalken, Prozent und ETA |
| **Face UID** | Kurze eindeutige IDs mit Spitzname, Region und Kommentaren |
| **Portable Edition** | `data\` neben der exe für Config, Datenbank und Logs |
| **Auto-Update** | Prüft [GitHub Releases](https://github.com/HFDWKJ/MediaManager/releases) beim Start |
| **UI** | DiskGenius-inspiriertes Dark Theme und Office-Style-Ribbon |

---

## Download

Vorkompilierte Binaries auf **[GitHub Releases](https://github.com/HFDWKJ/MediaManager/releases)**:

| Edition | Datei |
|---------|-------|
| Installer | `MediaManagerSetup_0.0.4.exe` |
| Portable Zip | `MediaManagerPortal_v0.0.4.zip` |

> [!NOTE]
> **Smart App Control:** Nicht signierte Builds können unter Windows 11 blockiert werden. SAC auf Testrechnern deaktivieren oder Installer für Produktion signieren.

---

## Schnellstart

### Voraussetzungen

- Python 3.10+
- Windows 11 (Windows 10+ unterstützt)

### Einrichtung & Start

```powershell
git clone https://github.com/HFDWKJ/MediaManager.git
cd MediaManager
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\create_test_data.py   # optional: Beispielordner
python src\main.py
```

### Workflow ausprobieren

1. **Add Library Root** — `test_data\library` oder Download-Ordner wählen.
2. **Discover / Scan** — `[Original Name]`-Entpack-Ordner indizieren.
3. **Review Name Matches** — verwerfen, als unterschiedlich markieren oder **Verify with Hash**.
4. **Reorganize ([Collections])** — Abflachen/Umbenennen in der Vorschau.
5. **Show in Explorer** — Ordner öffnen, wenn das Gerät online ist.

> [!TIP]
> Beim Start aus dem Quellcode öffnet **Download and update** die Releases-Seite im Browser. Gepackte Builds laden und installieren in der App.

---

## Entwicklung mit Cursor & Vibe Coding

Dieses Projekt ist ein **Praxisbeispiel für KI-gestützte Entwicklung** mit [Cursor](https://cursor.com) und **Vibe Coding**: Absicht in natürlicher Sprache beschreiben, Agent implementieren lassen, durch Ausführen und Feedback verfeinern.

| Phase | Vorgehen |
|-------|----------|
| **Planung** | [`media_manager_plan.md`](media_manager_plan.md) — phasenweise Prompts pro Meilenstein |
| **Implementierung** | Agent baute `core/`, `gui/`, Packaging-Skripte und Release-Flow schrittweise |
| **UI-Iteration** | Screenshot-Feedback (Ribbon, Fortschrittsbalken, Filter) |
| **Release-Tracking** | [`docs/ROADMAP.md`](docs/ROADMAP.md) + GitHub Issues / Milestones |

**Typische Schleife:** Prompt → Agent bearbeitet → `MediaManager.exe` ausführen → Screenshot/Fehler → Release.

> Englische Dokumentation: **[README.md § Built with Cursor](README.md#built-with-cursor--vibe-coding)**

### Praktische Hinweise

- Lebendigen Plan (`media_manager_plan.md`) für stabilen Agent-Kontext über Sessions hinweg pflegen.
- **Gepackte** Nuitka-Builds früh testen — Laufzeit-Erkennung unterscheidet sich von `python src\main.py`.
- Packaging-Regel: **nur Nuitka**, kein Inno Setup.
- Öffentliche GitHub Releases vereinfachen Auto-Update (kein Token nötig).

---

## Build (Nuitka)

Build-Skripte installieren Abhängigkeiten automatisch. Nuitka nutzt MSVC wenn verfügbar, sonst MinGW64.

### Anwendung

```powershell
.\scripts\build_nuitka.ps1              # dist\MediaManager\MediaManager.exe
.\scripts\build_nuitka.ps1 -Mode onefile  # dist\MediaManager.exe
```

### Installer

```powershell
.\scripts\build_installer.ps1
# → dist_installer\MediaManagerSetup_0.0.4.exe
```

Stille Flags für In-App-Updates: `/VERYSILENT`, `/SUPPRESSMSGBOXES`, `/NORESTART`, `/CLOSEAPPLICATIONS`, optional `/DIR=...`.

### Portable Zip

```powershell
.\scripts\build_portal.ps1
# → dist_portal\MediaManagerPortal_v0.0.4.zip
```

---

## Konfiguration und Datenpfade

**Installierte Edition**

| Element | Pfad |
|---------|------|
| Config | `%APPDATA%\MediaManager\config.json` |
| Datenbank | `%APPDATA%\MediaManager\catalog.db` |
| Logs | `%APPDATA%\MediaManager\logs\` |

**Portable Edition** — `portable.marker` neben `MediaManager.exe` oder Portal-Build:

| Element | Pfad |
|---------|------|
| Config | `data\config.json` |
| Datenbank | `data\catalog.db` |
| Logs | `data\logs\` |

Zum Migrieren **gesamten Ordner** (inkl. `data\`) kopieren.

---

## Anwendungs-Updates

- **Startprüfung** (standardmäßig an) und **Options → Check for updates…**
- Deaktivieren unter **Settings → Updates**
- Release-Tag `v0.0.4`; Release Notes im Update-Dialog
- Private Repos: `update.github_token` in Config oder `GITHUB_TOKEN` Umgebungsvariable

---

## Projektstruktur

```text
src/
  main.py              Einstiegspunkt
  core/                Datenbank, Scan, Abgleich, Reorganisieren, Updates
  gui/                 PyQt6 UI
  installer/           Nuitka-Setup-Assistent
  utils/               Config, Logging, Pfade
assets/                App-Icon
scripts/               Build- und Hilfsskripte
docs/ROADMAP.md        Meilenstein-Checkliste
media_manager_plan.md  Cursor-Entwicklungsplan nach Phasen
CHANGELOG.md           Release Notes (About-Dialog)
```

---

## Roadmap & Dokumentation

| Dokument | Beschreibung |
|----------|--------------|
| [README.md](README.md) | English |
| [README.zh-CN.md](README.zh-CN.md) | 简体中文 |
| [README.ja.md](README.ja.md) | 日本語 |
| [README.fr.md](README.fr.md) | Français |
| [README.ko.md](README.ko.md) | 한국어 |
| [README.es.md](README.es.md) | Español |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Versionspläne und v0.0.4-Checkliste |
| [CHANGELOG.md](CHANGELOG.md) | Release-Verlauf |
| [GitHub Milestones](https://github.com/HFDWKJ/MediaManager/milestones) | Issue-Tracking |

---

## Lizenz

Privates / persönliches Projekt von **Dong, Zhexi**. Verteilungsbedingungen siehe Repository-Einstellungen.
