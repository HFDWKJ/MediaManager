<p align="center">
  <img src="assets/media_manager_app_icon.png" alt="Media Manager" width="128"/>
</p>

<h1 align="center">Media Manager</h1>

<p align="center">
  <a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <strong>Français</strong> · <a href="README.de.md">Deutsch</a> · <a href="README.ko.md">한국어</a> · <a href="README.es.md">Español</a>
</p>

<p align="center">
  <a href="https://github.com/HFDWKJ/MediaManager/releases"><img src="https://img.shields.io/github/v/release/HFDWKJ/MediaManager?label=release&logo=github" alt="Release"/></a>
  <a href="https://github.com/HFDWKJ/MediaManager"><img src="https://img.shields.io/badge/platform-Windows-0078D6?logo=windows" alt="Windows"/></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white" alt="Python"/></a>
  <a href="https://www.riverbankcomputing.com/software/pyqt/"><img src="https://img.shields.io/badge/GUI-PyQt6-41CD52?logo=qt" alt="PyQt6"/></a>
</p>

<p align="center">
  Application Windows pour cataloguer des médias sur plusieurs disques et appareils,<br/>
  détecter les doublons de dossiers <code>[Original Name]</code> et réorganiser les téléchargements extraits.
</p>

<p align="center">
  <b>Version :</b> 0.0.3 · <b>Développeur :</b> Dong, Zhexi
</p>

---

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Téléchargement](#téléchargement)
- [Démarrage rapide](#démarrage-rapide)
- [Développement avec Cursor et Vibe Coding](#développement-avec-cursor-et-vibe-coding)
- [Compilation (Nuitka)](#compilation-nuitka)
- [Configuration et chemins de données](#configuration-et-chemins-de-données)
- [Mises à jour de l'application](#mises-à-jour-de-lapplication)
- [Structure du projet](#structure-du-projet)
- [Feuille de route et documentation](#feuille-de-route-et-documentation)
- [Licence](#licence)

---

## Fonctionnalités

| Domaine | Description |
|---------|-------------|
| **Bibliothèque multi-racines** | Indexation sur SSD/HDD, NAS, DAS et USB ; le catalogue reste utilisable hors ligne |
| **Détection de doublons** | Niveau 1 : correspondance floue `[Original Name]` · Niveau 2 : SHA-256 via **Verify with Hash** |
| **Réorganisation** | Aplatissement vers `[Collections]` avec modèles, barre de progression, pourcentage et ETA |
| **Face UID** | Identifiants courts uniques avec surnom, région et commentaires |
| **Édition portable** | Dossier `data\` à côté de l'exe pour config, base de données et journaux |
| **Mise à jour auto** | Vérification des [GitHub Releases](https://github.com/HFDWKJ/MediaManager/releases) au démarrage |
| **Interface** | Thème sombre inspiré de DiskGenius et ruban style Office |

---

## Téléchargement

Les binaires précompilés sont publiés sur **[GitHub Releases](https://github.com/HFDWKJ/MediaManager/releases)** :

| Édition | Fichier |
|---------|---------|
| Installateur | `MediaManagerSetup_0.0.3.exe` |
| Zip portable | `MediaManagerPortal_v0.0.3.zip` |

> [!NOTE]
> **Smart App Control :** les builds non signés peuvent être bloqués sous Windows 11. Désactivez SAC sur une machine de test ou signez l'installateur pour la production.

---

## Démarrage rapide

### Prérequis

- Python 3.10+
- Windows 11 (Windows 10+ pris en charge)

### Installation et exécution

```powershell
git clone https://github.com/HFDWKJ/MediaManager.git
cd MediaManager
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\create_test_data.py   # optionnel : dossiers d'exemple
python src\main.py
```

### Parcours d'essai

1. **Add Library Root** — pointez vers `test_data\library` ou votre dossier de téléchargements.
2. **Discover / Scan** — indexez les dossiers d'extraction `[Original Name]`.
3. **Review Name Matches** — ignorez, marquez comme différent ou **Verify with Hash**.
4. **Reorganize ([Collections])** — prévisualisez l'aplatissement et le renommage.
5. **Show in Explorer** — ouvrez le dossier lorsque l'appareil est en ligne.

> [!TIP]
> En exécution depuis les sources, **Download and update** ouvre la page Releases dans le navigateur. Les builds packagés téléchargent et installent dans l'application.

---

## Développement avec Cursor et Vibe Coding

Ce projet est un **exemple concret de développement assisté par IA** avec [Cursor](https://cursor.com) et **Vibe Coding** : décrire l'intention en langage naturel, laisser l'Agent implémenter, puis affiner en exécutant l'application et en donnant du retour.

| Étape | Approche |
|-------|----------|
| **Planification** | [`media_manager_plan.md`](media_manager_plan.md) — prompts par phase pour chaque jalon |
| **Implémentation** | L'Agent a construit `core/`, `gui/`, les scripts de packaging et le flux de release |
| **Itération UI** | Retours par captures d'écran (ruban, barre de progression, filtres) |
| **Suivi des releases** | [`docs/ROADMAP.md`](docs/ROADMAP.md) + GitHub Issues / Milestones |

**Boucle typique :** Prompt → éditions Agent → exécuter `MediaManager.exe` → capture / erreur → publication.

> Documentation en anglais : **[README.md § Built with Cursor](README.md#built-with-cursor--vibe-coding)**

### Notes pratiques

- Conserver un plan vivant (`media_manager_plan.md`) pour un contexte Agent stable entre sessions.
- Tester tôt les builds **packagés** Nuitka — la détection d'exécution diffère de `python src\main.py`.
- Règle de packaging : **Nuitka uniquement**, pas Inno Setup.
- Les GitHub Releases publics simplifient la mise à jour automatique (sans token).

---

## Compilation (Nuitka)

Les scripts installent les dépendances automatiquement. Nuitka utilise MSVC si disponible, sinon MinGW64.

### Application

```powershell
.\scripts\build_nuitka.ps1              # dist\MediaManager\MediaManager.exe
.\scripts\build_nuitka.ps1 -Mode onefile  # dist\MediaManager.exe
```

### Installateur

```powershell
.\scripts\build_installer.ps1
# → dist_installer\MediaManagerSetup_0.0.3.exe
```

Flags silencieux pour les mises à jour in-app : `/VERYSILENT`, `/SUPPRESSMSGBOXES`, `/NORESTART`, `/CLOSEAPPLICATIONS`, optionnel `/DIR=...`.

### Zip portable

```powershell
.\scripts\build_portal.ps1
# → dist_portal\MediaManagerPortal_v0.0.3.zip
```

---

## Configuration et chemins de données

**Édition installée**

| Élément | Chemin |
|---------|--------|
| Config | `%APPDATA%\MediaManager\config.json` |
| Base de données | `%APPDATA%\MediaManager\catalog.db` |
| Journaux | `%APPDATA%\MediaManager\logs\` |

**Édition portable** — `portable.marker` à côté de `MediaManager.exe`, ou build portal :

| Élément | Chemin |
|---------|--------|
| Config | `data\config.json` |
| Base de données | `data\catalog.db` |
| Journaux | `data\logs\` |

Copiez **le dossier entier** (y compris `data\`) pour migrer catalogue et paramètres.

---

## Mises à jour de l'application

- **Vérification au démarrage** (activée par défaut) et **Options → Check for updates…**
- Désactivation dans **Settings → Updates**
- Tag de release `v0.0.3` ; les notes apparaissent dans la boîte de dialogue de mise à jour
- Dépôts privés : `update.github_token` dans la config ou variable `GITHUB_TOKEN`

---

## Structure du projet

```text
src/
  main.py              Point d'entrée
  core/                Base de données, scan, correspondance, réorganisation, mises à jour
  gui/                 Interface PyQt6
  installer/           Assistant d'installation Nuitka
  utils/               Config, journaux, chemins
assets/                Icône de l'application
scripts/               Scripts de build et utilitaires
docs/ROADMAP.md        Liste des jalons
media_manager_plan.md  Plan de développement Cursor par phases
CHANGELOG.md           Notes de version (dialogue About)
```

---

## Feuille de route et documentation

| Document | Description |
|----------|-------------|
| [README.md](README.md) | English |
| [README.zh-CN.md](README.zh-CN.md) | 简体中文 |
| [README.ja.md](README.ja.md) | 日本語 |
| [README.de.md](README.de.md) | Deutsch |
| [README.ko.md](README.ko.md) | 한국어 |
| [README.es.md](README.es.md) | Español |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Plans de version et checklist v0.0.3 |
| [CHANGELOG.md](CHANGELOG.md) | Historique des releases |
| [GitHub Milestones](https://github.com/HFDWKJ/MediaManager/milestones) | Suivi des issues |

---

## Licence

Projet personnel / privé de **Dong, Zhexi**. Voir les paramètres du dépôt pour les conditions de distribution.
