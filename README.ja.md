<p align="center">
  <img src="assets/media_manager_app_icon.png" alt="Media Manager" width="128"/>
</p>

<h1 align="center">Media Manager</h1>

<p align="center">
  <a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <strong>日本語</strong> · <a href="README.fr.md">Français</a> · <a href="README.de.md">Deutsch</a> · <a href="README.ko.md">한국어</a> · <a href="README.es.md">Español</a>
</p>

<p align="center">
  <a href="https://github.com/HFDWKJ/MediaManager/releases"><img src="https://img.shields.io/github/v/release/HFDWKJ/MediaManager?label=release&logo=github" alt="Release"/></a>
  <a href="https://github.com/HFDWKJ/MediaManager"><img src="https://img.shields.io/badge/platform-Windows-0078D6?logo=windows" alt="Windows"/></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white" alt="Python"/></a>
  <a href="https://www.riverbankcomputing.com/software/pyqt/"><img src="https://img.shields.io/badge/GUI-PyQt6-41CD52?logo=qt" alt="PyQt6"/></a>
</p>

<p align="center">
  複数のドライブとデバイスにまたがるメディアをカタログ化し、<br/>
  <code>[Original Name]</code> フォルダの重複を検出し、展開済みダウンロードを整理する Windows デスクトップアプリ。
</p>

<p align="center">
  <b>バージョン：</b>0.0.3 · <b>開発者：</b>Dong, Zhexi
</p>

---

## 目次

- [機能概要](#機能概要)
- [ダウンロード](#ダウンロード)
- [クイックスタート](#クイックスタート)
- [Cursor と Vibe Coding による開発](#cursor-と-vibe-coding-による開発)
- [ビルド（Nuitka）](#ビルドnuitka)
- [設定とデータパス](#設定とデータパス)
- [アプリ内アップデート](#アプリ内アップデート)
- [プロジェクト構成](#プロジェクト構成)
- [ロードマップとドキュメント](#ロードマップとドキュメント)
- [ライセンス](#ライセンス)

---

## 機能概要

| 領域 | 説明 |
|------|------|
| **マルチルートライブラリ** | SSD/HDD、NAS、DAS、USB 上のフォルダをインデックス化。デバイスがオフラインでもカタログは利用可能 |
| **重複検出** | 第1段階：`[Original Name]` のあいまい一致 · 第2段階：**Verify with Hash** 選択時に SHA-256 |
| **整理** | 展開フォルダを `[Collections]` にフラット化。テンプレート、進捗バー、パーセント、ETA 対応 |
| **Face UID** | ニックネーム、地域、コメント付きの短い一意 ID |
| **ポータブル版** | exe 横の `data\` に設定、DB、ログを保存 |
| **自動更新** | 起動時に [GitHub Releases](https://github.com/HFDWKJ/MediaManager/releases) を確認 |
| **UI** | DiskGenius 風ダークテーマと Office スタイルのリボン |

---

## ダウンロード

ビルド済みバイナリは **[GitHub Releases](https://github.com/HFDWKJ/MediaManager/releases)** で公開：

| 版 | ファイル |
|----|----------|
| インストーラー | `MediaManagerSetup_0.0.3.exe` |
| ポータブル zip | `MediaManagerPortal_v0.0.3.zip` |

> [!NOTE]
> **Smart App Control：** 署名のない exe は Windows 11 でブロックされる場合があります。テスト機では SAC をオフにするか、本番用にインストーラーに署名してください。

---

## クイックスタート

### 要件

- Python 3.10+
- Windows 11（Windows 10+ 対応）

### セットアップと実行

```powershell
git clone https://github.com/HFDWKJ/MediaManager.git
cd MediaManager
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\create_test_data.py   # 任意：サンプルフォルダ
python src\main.py
```

### お試しワークフロー

1. **Add Library Root** — `test_data\library` またはダウンロードフォルダを指定。
2. **Discover / Scan** — `[Original Name]` 展開フォルダをインデックス化。
3. **Review Name Matches** — 却下、別物としてマーク、または **Verify with Hash**。
4. **Reorganize ([Collections])** — フラット化・リネームをプレビュー。
5. **Show in Explorer** — デバイスがオンラインのときフォルダを開く。

> [!TIP]
> ソースから実行する場合、**Download and update** を選ぶとブラウザで Releases ページが開きます。パッケージ版はアプリ内でダウンロード・インストールします。

---

## Cursor と Vibe Coding による開発

本プロジェクトは [Cursor](https://cursor.com) と **Vibe Coding**（自然言語で意図を伝え、Agent が実装、実行とフィードバックで改善）による **AI 支援開発の実践例** です。

| 段階 | 方法 |
|------|------|
| **計画** | [`media_manager_plan.md`](media_manager_plan.md) — マイルストーンごとの段階的プロンプト |
| **実装** | Agent が `core/`、`gui/`、パッケージング、リリースフローを段階的に構築 |
| **UI 反復** | スクリーンショットによるフィードバック（リボン、進捗バー、フィルター） |
| **リリース管理** | [`docs/ROADMAP.md`](docs/ROADMAP.md) + GitHub Issues / Milestones |

**典型的なループ：** プロンプト → Agent が編集 → `MediaManager.exe` を実行 → スクリーンショット／エラー報告 → リリース。

> 英語ドキュメント：**[README.md § Built with Cursor](README.md#built-with-cursor--vibe-coding)**

### 実践上の注意

- 生きた計画書（`media_manager_plan.md`）でセッション間の Agent コンテキストを安定させる。
- **パッケージ版** Nuitka ビルドを早めにテスト — `python src\main.py` とは実行環境が異なる。
- パッケージング規則：**Nuitka のみ**、Inno Setup 不使用。
- 公開 GitHub Releases なら自動更新にトークン不要。

---

## ビルド（Nuitka）

ビルドスクリプトが依存関係を自動インストール。Nuitka は MSVC を優先、なければ MinGW64。

### アプリケーション

```powershell
.\scripts\build_nuitka.ps1              # dist\MediaManager\MediaManager.exe
.\scripts\build_nuitka.ps1 -Mode onefile  # dist\MediaManager.exe
```

### インストーラー

```powershell
.\scripts\build_installer.ps1
# → dist_installer\MediaManagerSetup_0.0.3.exe
```

アプリ内更新のサイレントフラグ：`/VERYSILENT`、`/SUPPRESSMSGBOXES`、`/NORESTART`、`/CLOSEAPPLICATIONS`、任意で `/DIR=...`。

### ポータブル zip

```powershell
.\scripts\build_portal.ps1
# → dist_portal\MediaManagerPortal_v0.0.3.zip
```

---

## 設定とデータパス

**インストール版**

| 項目 | パス |
|------|------|
| 設定 | `%APPDATA%\MediaManager\config.json` |
| データベース | `%APPDATA%\MediaManager\catalog.db` |
| ログ | `%APPDATA%\MediaManager\logs\` |

**ポータブル版** — `MediaManager.exe` 横に `portable.marker`、または portal ビルド：

| 項目 | パス |
|------|------|
| 設定 | `data\config.json` |
| データベース | `data\catalog.db` |
| ログ | `data\logs\` |

別 PC へ移す場合は **`data\` を含むフォルダ全体** をコピーしてください。

---

## アプリ内アップデート

- **起動時チェック**（デフォルト ON）と **Options → Check for updates…**
- **Settings → Updates** で無効化可能
- リリースタグ `v0.0.3`；Release ノートは更新ダイアログに表示
- プライベートリポジトリ：config の `update.github_token` または `GITHUB_TOKEN` 環境変数

---

## プロジェクト構成

```text
src/
  main.py              エントリポイント
  core/                DB、スキャン、マッチ、整理、更新
  gui/                 PyQt6 UI
  installer/           Nuitka セットアップウィザード
  utils/               設定、ログ、パス
assets/                アプリアイコン
scripts/               ビルドとヘルパー
docs/ROADMAP.md        マイルストーン一覧
media_manager_plan.md  Cursor 段階的開発計画
CHANGELOG.md           リリースノート（About ダイアログ）
```

---

## ロードマップとドキュメント

| ドキュメント | 説明 |
|--------------|------|
| [README.md](README.md) | English |
| [README.zh-CN.md](README.zh-CN.md) | 简体中文 |
| [README.fr.md](README.fr.md) | Français |
| [README.de.md](README.de.md) | Deutsch |
| [README.ko.md](README.ko.md) | 한국어 |
| [README.es.md](README.es.md) | Español |
| [docs/ROADMAP.md](docs/ROADMAP.md) | バージョン計画と v0.0.3 チェックリスト |
| [CHANGELOG.md](CHANGELOG.md) | リリース履歴 |
| [GitHub Milestones](https://github.com/HFDWKJ/MediaManager/milestones) | Issue 追跡 |

---

## ライセンス

**Dong, Zhexi** の個人／プライベートプロジェクト。配布条件はリポジトリ設定を参照。
