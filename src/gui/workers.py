"""Background workers for scan and hash operations."""

from __future__ import annotations

import tempfile
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from core.database import Database
from core.device_manager import refresh_all_device_status
from core.duplicate_finder import verify_extraction_folders
from core.extraction_import import discover_previews_all_roots, discover_previews_for_root
from core.folder_preview import FolderPreview
from core.reorganize import build_reorganize_plan, execute_reorganize
from core.update_checker import DEFAULT_GITHUB_REPO, ReleaseAsset, UpdateCheckError, fetch_latest_release
from core.update_installer import download_release_asset
from utils.paths import is_portable_mode


class DiscoverWorker(QThread):
    """Discover folders on disk for approval (no database writes)."""
    finished_ok = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, db: Database, config: dict, root_id: int | None = None) -> None:
        super().__init__()
        self.db = db
        self.config = config
        self.root_id = root_id

    def run(self) -> None:
        try:
            refresh_all_device_status(self.db)
            if self.root_id is not None:
                previews = discover_previews_for_root(self.db, self.root_id, self.config)
            else:
                previews = discover_previews_all_roots(self.db, self.config)
            self.finished_ok.emit(previews)
        except Exception as e:
            self.error.emit(str(e))


class HashVerifyWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished_ok = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, db: Database, extraction_ids: list[int]) -> None:
        super().__init__()
        self.db = db
        self.extraction_ids = extraction_ids

    def run(self) -> None:
        try:
            def prog(cur: int, total: int, name: str) -> None:
                self.progress.emit(cur, total, name)

            result = verify_extraction_folders(self.db, self.extraction_ids, progress=prog)
            self.finished_ok.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class ReorganizeWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished_ok = pyqtSignal(bool)
    error = pyqtSignal(str)

    def __init__(self, db: Database, plan, config: dict) -> None:
        super().__init__()
        self.db = db
        self.plan = plan
        self.config = config

    def run(self) -> None:
        try:
            def prog(cur: int, total: int, name: str) -> None:
                self.progress.emit(cur, total, name)

            ok = execute_reorganize(self.db, self.plan, self.config, prog)
            self.finished_ok.emit(ok)
        except Exception as e:
            self.error.emit(str(e))


class UpdateCheckWorker(QThread):
    finished_ok = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, github_repo: str = DEFAULT_GITHUB_REPO) -> None:
        super().__init__()
        self.github_repo = github_repo

    def run(self) -> None:
        try:
            release = fetch_latest_release(
                self.github_repo,
                portable=is_portable_mode(),
            )
            self.finished_ok.emit(release)
        except UpdateCheckError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(str(e))


class UpdateDownloadWorker(QThread):
    progress = pyqtSignal(int, int)
    finished_ok = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, release: ReleaseAsset) -> None:
        super().__init__()
        self.release = release

    def run(self) -> None:
        try:
            dest = Path(tempfile.mkdtemp(prefix="mm_dl_"))

            def prog(cur: int, total: int) -> None:
                self.progress.emit(cur, total)

            path = download_release_asset(self.release, dest, progress=prog)
            self.finished_ok.emit(str(path))
        except Exception as e:
            self.error.emit(str(e))
