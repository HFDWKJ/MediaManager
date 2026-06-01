<p align="center">
  <img src="assets/media_manager_app_icon.png" alt="Media Manager" width="128"/>
</p>

<h1 align="center">Media Manager</h1>

<p align="center">
  <a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.fr.md">Français</a> · <a href="README.de.md">Deutsch</a> · <strong>한국어</strong> · <a href="README.es.md">Español</a>
</p>

<p align="center">
  <a href="https://github.com/HFDWKJ/MediaManager/releases"><img src="https://img.shields.io/github/v/release/HFDWKJ/MediaManager?label=release&logo=github" alt="Release"/></a>
  <a href="https://github.com/HFDWKJ/MediaManager"><img src="https://img.shields.io/badge/platform-Windows-0078D6?logo=windows" alt="Windows"/></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white" alt="Python"/></a>
  <a href="https://www.riverbankcomputing.com/software/pyqt/"><img src="https://img.shields.io/badge/GUI-PyQt6-41CD52?logo=qt" alt="PyQt6"/></a>
</p>

<p align="center">
  여러 드라이브와 장치에 흩어진 미디어를 카탈로그화하고,<br/>
  <code>[Original Name]</code> 폴더 중복을 감지하며, 압축 해제된 다운로드를 정리하는 Windows 데스크톱 앱.
</p>

<p align="center">
  <b>버전:</b> 0.0.3 · <b>개발자:</b> Dong, Zhexi
</p>

---

## 목차

- [기능 개요](#기능-개요)
- [다운로드](#다운로드)
- [빠른 시작](#빠른-시작)
- [Cursor와 Vibe Coding으로 개발](#cursor와-vibe-coding으로-개발)
- [빌드 (Nuitka)](#빌드-nuitka)
- [설정 및 데이터 경로](#설정-및-데이터-경로)
- [앱 내 업데이트](#앱-내-업데이트)
- [프로젝트 구조](#프로젝트-구조)
- [로드맵 및 문서](#로드맵-및-문서)
- [라이선스](#라이선스)

---

## 기능 개요

| 영역 | 설명 |
|------|------|
| **다중 루트 라이브러리** | SSD/HDD, NAS, DAS, USB 폴더 인덱싱; 장치 오프라인 시에도 카탈로그 사용 가능 |
| **중복 감지** | 1단계: `[Original Name]` 퍼지 매칭 · 2단계: **Verify with Hash** 선택 시 SHA-256 |
| **재구성** | 압축 해제 폴더를 `[Collections]`로 평탄화; 템플릿, 진행률 표시줄, 백분율, ETA |
| **Face UID** | 닉네임, 지역, 코멘트가 있는 짧은 고유 ID |
| **포터블 에디션** | exe 옆 `data\`에 설정, DB, 로그 저장 |
| **자동 업데이트** | 시작 시 [GitHub Releases](https://github.com/HFDWKJ/MediaManager/releases) 확인 |
| **UI** | DiskGenius 스타일 다크 테마 및 Office 스타일 리본 |

---

## 다운로드

빌드된 바이너리는 **[GitHub Releases](https://github.com/HFDWKJ/MediaManager/releases)** 에서 제공:

| 에디션 | 파일 |
|--------|------|
| 설치판 | `MediaManagerSetup_0.0.3.exe` |
| 포터블 zip | `MediaManagerPortal_v0.0.3.zip` |

> [!NOTE]
> **Smart App Control:** 서명되지 않은 exe는 Windows 11에서 차단될 수 있습니다. 테스트 PC에서 SAC를 끄거나, 배포용으로 설치 프로그램에 서명하세요.

---

## 빠른 시작

### 요구 사항

- Python 3.10+
- Windows 11 (Windows 10+ 지원)

### 설치 및 실행

```powershell
git clone https://github.com/HFDWKJ/MediaManager.git
cd MediaManager
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\create_test_data.py   # 선택: 샘플 폴더
python src\main.py
```

### 워크플로우 체험

1. **Add Library Root** — `test_data\library` 또는 다운로드 폴더 지정.
2. **Discover / Scan** — `[Original Name]` 압축 해제 폴더 인덱싱.
3. **Review Name Matches** — 무시, 다름으로 표시, 또는 **Verify with Hash**.
4. **Reorganize ([Collections])** — 평탄화/이름 변경 미리보기.
5. **Show in Explorer** — 장치 온라인 시 폴더 열기.

> [!TIP]
> 소스에서 실행할 때 **Download and update** 는 브라우저에서 Releases 페이지를 엽니다. 패키징된 빌드는 앱 내에서 다운로드 및 설치합니다.

---

## Cursor와 Vibe Coding으로 개발

이 프로젝트는 [Cursor](https://cursor.com)와 **Vibe Coding**(자연어로 의도 설명 → Agent 구현 → 실행 및 피드백으로 개선)을 활용한 **AI 지원 개발 실전 사례**입니다.

| 단계 | 방법 |
|------|------|
| **계획** | [`media_manager_plan.md`](media_manager_plan.md) — 마일스톤별 단계적 프롬프트 |
| **구현** | Agent가 `core/`, `gui/`, 패키징 스크립트, 릴리스 흐름을 단계적으로 구축 |
| **UI 반복** | 스크린샷 피드백(리본, 진행률 표시줄, 필터) |
| **릴리스 추적** | [`docs/ROADMAP.md`](docs/ROADMAP.md) + GitHub Issues / Milestones |

**일반적인 루프:** 프롬프트 → Agent 편집 → `MediaManager.exe` 실행 → 스크린샷/오류 피드백 → 릴리스.

> 영어 문서: **[README.md § Built with Cursor](README.md#built-with-cursor--vibe-coding)**

### 실무 팁

- 살아 있는 계획서(`media_manager_plan.md`)로 세션 간 Agent 컨텍스트 유지.
- **패키징된** Nuitka 빌드를 일찍 테스트 — `python src\main.py`와 런타임 감지가 다름.
- 패키징 규칙: **Nuitka만**, Inno Setup 사용 안 함.
- 공개 GitHub Releases는 자동 업데이트를 단순화(토큰 불필요).

---

## 빌드 (Nuitka)

빌드 스크립트가 의존성을 자동 설치. Nuitka는 MSVC 우선, 없으면 MinGW64.

### 애플리케이션

```powershell
.\scripts\build_nuitka.ps1              # dist\MediaManager\MediaManager.exe
.\scripts\build_nuitka.ps1 -Mode onefile  # dist\MediaManager.exe
```

### 설치 프로그램

```powershell
.\scripts\build_installer.ps1
# → dist_installer\MediaManagerSetup_0.0.3.exe
```

앱 내 업데이트 무음 플래그: `/VERYSILENT`, `/SUPPRESSMSGBOXES`, `/NORESTART`, `/CLOSEAPPLICATIONS`, 선택 `/DIR=...`.

### 포터블 zip

```powershell
.\scripts\build_portal.ps1
# → dist_portal\MediaManagerPortal_v0.0.3.zip
```

---

## 설정 및 데이터 경로

**설치판**

| 항목 | 경로 |
|------|------|
| 설정 | `%APPDATA%\MediaManager\config.json` |
| 데이터베이스 | `%APPDATA%\MediaManager\catalog.db` |
| 로그 | `%APPDATA%\MediaManager\logs\` |

**포터블판** — `MediaManager.exe` 옆 `portable.marker` 또는 portal 빌드:

| 항목 | 경로 |
|------|------|
| 설정 | `data\config.json` |
| 데이터베이스 | `data\catalog.db` |
| 로그 | `data\logs\` |

다른 PC로 옮길 때 **`data\` 포함 전체 폴더**를 복사하세요.

---

## 앱 내 업데이트

- **시작 시 확인**(기본 켜짐) 및 **Options → Check for updates…**
- **Settings → Updates**에서 끄기
- 릴리스 태그 `v0.0.3`; 릴리스 노트는 업데이트 대화상자에 표시
- 비공개 저장소: config의 `update.github_token` 또는 `GITHUB_TOKEN` 환경 변수

---

## 프로젝트 구조

```text
src/
  main.py              진입점
  core/                DB, 스캔, 매칭, 재구성, 업데이트
  gui/                 PyQt6 UI
  installer/           Nuitka 설치 마법사
  utils/               설정, 로깅, 경로
assets/                앱 아이콘
scripts/               빌드 및 헬퍼 스크립트
docs/ROADMAP.md        마일스톤 체크리스트
media_manager_plan.md  Cursor 단계별 개발 계획
CHANGELOG.md           릴리스 노트 (About 대화상자)
```

---

## 로드맵 및 문서

| 문서 | 설명 |
|------|------|
| [README.md](README.md) | English |
| [README.zh-CN.md](README.zh-CN.md) | 简体中文 |
| [README.ja.md](README.ja.md) | 日本語 |
| [README.fr.md](README.fr.md) | Français |
| [README.de.md](README.de.md) | Deutsch |
| [README.es.md](README.es.md) | Español |
| [docs/ROADMAP.md](docs/ROADMAP.md) | 버전 계획 및 v0.0.3 체크리스트 |
| [CHANGELOG.md](CHANGELOG.md) | 릴리스 기록 |
| [GitHub Milestones](https://github.com/HFDWKJ/MediaManager/milestones) | 이슈 추적 |

---

## 라이선스

**Dong, Zhexi**의 개인/비공개 프로젝트. 배포 조건은 저장소 설정을 참조하세요.
