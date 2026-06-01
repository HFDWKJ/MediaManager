<p align="center">
  <img src="assets/media_manager_app_icon.png" alt="Media Manager" width="128"/>
</p>

<h1 align="center">Media Manager</h1>

<p align="center">
  <a href="README.md">English</a> · <strong>简体中文</strong> · <a href="README.ja.md">日本語</a> · <a href="README.fr.md">Français</a> · <a href="README.de.md">Deutsch</a> · <a href="README.ko.md">한국어</a> · <a href="README.es.md">Español</a>
</p>

<p align="center">
  <a href="https://github.com/HFDWKJ/MediaManager/releases"><img src="https://img.shields.io/github/v/release/HFDWKJ/MediaManager?label=release&logo=github" alt="Release"/></a>
  <a href="https://github.com/HFDWKJ/MediaManager"><img src="https://img.shields.io/badge/platform-Windows-0078D6?logo=windows" alt="Windows"/></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white" alt="Python"/></a>
  <a href="https://www.riverbankcomputing.com/software/pyqt/"><img src="https://img.shields.io/badge/GUI-PyQt6-41CD52?logo=qt" alt="PyQt6"/></a>
</p>

<p align="center">
  Windows 桌面媒体管理工具：跨多块硬盘与设备建立统一目录，<br/>
  识别 <code>[Original Name]</code> 文件夹重复，并整理解压后的下载内容。
</p>

<p align="center">
  <b>版本：</b>0.0.3 · <b>开发者：</b>Dong, Zhexi
</p>

---

## 目录

- [功能概览](#功能概览)
- [下载安装](#下载安装)
- [快速开始](#快速开始)
- [使用 Cursor 与 Vibe Coding 开发](#使用-cursor-与-vibe-coding-开发)
- [打包构建（Nuitka）](#打包构建nuitka)
- [配置与数据路径](#配置与数据路径)
- [应用内更新](#应用内更新)
- [项目结构](#项目结构)
- [路线图与文档](#路线图与文档)
- [许可说明](#许可说明)

---

## 功能概览

| 模块 | 说明 |
|------|------|
| **多根目录库** | 支持 SSD/HDD、NAS、DAS、USB；设备离线时目录仍可使用 |
| **重复检测** | 第一层：`[Original Name]` 模糊匹配 · 第二层：用户触发 SHA-256 哈希校验 |
| **整理重组** | 将解压文件夹扁平化到 `[Collections]`，支持模板、进度条、百分比与 ETA |
| **Face UID** | 短唯一 ID，附带昵称、地区与备注 |
| **便携版** | 在 exe 旁使用 `data\` 存放配置、数据库与日志 |
| **自动更新** | 启动时检查 [GitHub Releases](https://github.com/HFDWKJ/MediaManager/releases) |
| **界面** | DiskGenius 风格暗色主题 + Office 风格 Ribbon |

---

## 下载安装

预编译安装包发布于 **[GitHub Releases](https://github.com/HFDWKJ/MediaManager/releases)**：

| 版本 | 文件名 |
|------|--------|
| 安装版 | `MediaManagerSetup_0.0.3.exe` |
| 便携版 zip | `MediaManagerPortal_v0.0.3.zip` |

> [!NOTE]
> **Smart App Control：** 未签名的 exe 可能在 Windows 11 上被拦截。测试机可暂时关闭 SAC，正式分发建议做代码签名。

---

## 快速开始

### 环境要求

- Python 3.10+
- Windows 11（Windows 10+ 可用）

### 安装与运行

```powershell
git clone https://github.com/HFDWKJ/MediaManager.git
cd MediaManager
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\create_test_data.py   # 可选：生成示例文件夹
python src\main.py
```

### 推荐试用流程

1. **Add Library Root** — 选择 `test_data\library` 或你的下载目录。
2. **Discover / Scan** — 扫描并索引 `[Original Name]` 解压文件夹。
3. **Review Name Matches** — 忽略、标记不同，或 **Verify with Hash**。
4. **Reorganize ([Collections])** — 预览扁平化与重命名。
5. **Show in Explorer** — 设备在线时在资源管理器中打开。

> [!TIP]
> 从源码运行时，选择 **Download and update** 会在浏览器打开 Releases 页面；打包后的 exe 支持应用内下载与静默安装。

---

## 使用 Cursor 与 Vibe Coding 开发

本项目是在 [Cursor](https://cursor.com) 中通过 **Vibe Coding**（自然语言驱动 + AI Agent 写代码 + 人工验收）完整迭代出来的 **个人工具 + AI 结对编程** 样本。

| 阶段 | 做法 |
|------|------|
| **需求与计划** | [`media_manager_plan.md`](media_manager_plan.md) 按 Phase 拆分，逐步交给 Agent |
| **功能实现** | Agent 依次完成 `core/`、`gui/`、打包脚本与 GitHub 发布流程 |
| **界面迭代** | 截图反馈驱动（Ribbon、进度条、筛选栏等），无需手写全部 UI |
| **版本跟踪** | [`docs/ROADMAP.md`](docs/ROADMAP.md) + GitHub Issues / Milestones |

### 典型开发循环

1. **描述需求** — 粘贴 `media_manager_plan.md` 中的 Phase，或用中文/英文描述 bug 或功能。
2. **Agent 改代码** — Cursor 修改源码、脚本与文档，必要时运行构建。
3. **本机验证** — 运行 `python src\main.py` 或打包后的 `MediaManager.exe`。
4. **反馈调整** — 提供截图、期望行为或报错信息，Agent 继续修改。
5. **发布** — 更新 `src/version.py`、`CHANGELOG.md`，Nuitka 打包并上传 Releases。

### 实践经验

- **保持一份活文档** — `media_manager_plan.md` 让 Agent 在长会话中保持上下文一致。
- **分阶段推进** — 数据库 → 扫描 → GUI → 打包，减少错误假设。
- **尽早测打包版** — Nuitka 使用 `__compiled__`，与 `python src\main.py` 行为不同；安装器与自动更新必须在 exe 上验证。
- **Cursor 用户规则** — 例如「仅 Nuitka，不用 Inno Setup」可在各次对话中保持一致。
- **公开仓库简化更新** — GitHub Releases API 无需 Token 即可检测与下载。

> English documentation: **[README.md § Built with Cursor](README.md#built-with-cursor--vibe-coding)**

---

## 打包构建（Nuitka）

**打包规则：仅使用 Nuitka**，不使用 Inno Setup。脚本会自动安装依赖；Windows 上优先 MSVC，否则 MinGW64。

### 应用程序

```powershell
.\scripts\build_nuitka.ps1              # dist\MediaManager\MediaManager.exe
.\scripts\build_nuitka.ps1 -Mode onefile  # dist\MediaManager.exe
```

### 安装包

```powershell
.\scripts\build_installer.ps1
# → dist_installer\MediaManagerSetup_0.0.3.exe
```

应用内更新使用的静默参数：`/VERYSILENT`、`/SUPPRESSMSGBOXES`、`/NORESTART`、`/CLOSEAPPLICATIONS`，可选 `/DIR=...`。

### 便携版 zip

```powershell
.\scripts\build_portal.ps1
# → dist_portal\MediaManagerPortal_v0.0.3.zip
```

---

## 配置与数据路径

**安装版（默认）**

| 项目 | 路径 |
|------|------|
| 配置 | `%APPDATA%\MediaManager\config.json` |
| 数据库 | `%APPDATA%\MediaManager\catalog.db` |
| 日志 | `%APPDATA%\MediaManager\logs\` |

**便携版** — 在 `MediaManager.exe` 旁放置 `portable.marker`，或使用 portal 构建脚本：

| 项目 | 路径 |
|------|------|
| 配置 | `data\config.json` |
| 数据库 | `data\catalog.db` |
| 日志 | `data\logs\` |

迁移时请复制**整个文件夹**（含 `data\`）。

---

## 应用内更新

- 启动时自动检查（默认开启），或 **Options → Check for updates…**
- 在 **Settings → Updates** 中可关闭
- Release 标签如 `v0.0.3`；Release 说明会显示在更新对话框
- 私有仓库需在 config 中设置 `update.github_token`，或设置 `GITHUB_TOKEN` 环境变量

---

## 项目结构

```text
src/
  main.py              程序入口
  core/                数据库、扫描、匹配、整理、更新
  gui/                 PyQt6 界面
  installer/           Nuitka 安装向导
  utils/               配置、日志、路径
assets/                应用图标
scripts/               构建与辅助脚本
docs/ROADMAP.md        里程碑清单
media_manager_plan.md  Cursor 分阶段开发计划
CHANGELOG.md           更新日志（About 对话框中显示）
```

---

## 路线图与文档

| 文档 | 说明 |
|------|------|
| [README.md](README.md) | English |
| [README.ja.md](README.ja.md) | 日本語 |
| [README.fr.md](README.fr.md) | Français |
| [README.de.md](README.de.md) | Deutsch |
| [README.ko.md](README.ko.md) | 한국어 |
| [README.es.md](README.es.md) | Español |
| [docs/ROADMAP.md](docs/ROADMAP.md) | 版本计划与 v0.0.3 任务清单 |
| [CHANGELOG.md](CHANGELOG.md) | 版本更新记录 |
| [GitHub Milestones](https://github.com/HFDWKJ/MediaManager/milestones) | Issue 跟踪 |
| [media_manager_plan.md](media_manager_plan.md) | 完整 Cursor 开发计划 |

---

## 许可说明

**Dong, Zhexi** 的个人/私有项目。分发条款见仓库设置。
