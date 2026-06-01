"""Dialogs for checking and applying application updates."""

from __future__ import annotations

import sys
import webbrowser

from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from core.update_checker import ReleaseAsset
from core.update_installer import UpdateInstallError, can_apply_in_app_update
from gui.workers import UpdateCheckWorker, UpdateDownloadWorker
from version import __version__


def _releases_page_url(repo: str) -> str:
    return f"https://github.com/{repo}/releases"


class UpdateAvailableDialog(QDialog):
    """Prompt when a newer version is available."""

    def __init__(
        self,
        release: ReleaseAsset,
        *,
        repo: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.release = release
        self.repo = repo
        self._accepted_update = False
        self._later_chosen = False

        self.setWindowTitle("Update available")
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                f"A new version is available.\n\n"
                f"Installed: {__version__}\n"
                f"Latest: {release.version}"
            )
        )

        if release.body:
            notes = QTextBrowser()
            notes.setMaximumHeight(160)
            notes.setMarkdown(release.body)
            notes.setOpenExternalLinks(True)
            layout.addWidget(QLabel("Release notes:"))
            layout.addWidget(notes)

        layout.addWidget(
            QLabel(f"Package: {release.filename}")
        )

        if not can_apply_in_app_update():
            layout.addWidget(
                QLabel(
                    "Running from source — open the release page to download the installer "
                    "or portable package."
                )
            )

        buttons = QDialogButtonBox()
        self._update_btn = QPushButton("Download and update")
        self._later_btn = QPushButton("Later")
        self._cancel_btn = QPushButton("Cancel")
        buttons.addButton(self._update_btn, QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton(self._later_btn, QDialogButtonBox.ButtonRole.RejectRole)
        buttons.addButton(self._cancel_btn, QDialogButtonBox.ButtonRole.RejectRole)
        self._update_btn.clicked.connect(self._on_update)
        self._later_btn.clicked.connect(self._on_later)
        self._cancel_btn.clicked.connect(self.reject)
        layout.addWidget(buttons)

    def wants_update(self) -> bool:
        return self._accepted_update

    def dismissed_later(self) -> bool:
        return self._later_chosen

    def _on_update(self) -> None:
        if not can_apply_in_app_update():
            webbrowser.open(_releases_page_url(self.repo))
            self._accepted_update = True
            self.accept()
            return
        self._accepted_update = True
        self.accept()

    def _on_later(self) -> None:
        self._later_chosen = True
        self.reject()


class UpdateProgressDialog(QDialog):
    """Download and apply an update package."""

    def __init__(
        self,
        release: ReleaseAsset,
        *,
        github_token: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.release = release
        self._github_token = github_token
        self._worker: UpdateDownloadWorker | None = None

        self.setWindowTitle("Downloading update")
        self.setMinimumWidth(420)
        self.setModal(True)

        layout = QVBoxLayout(self)
        self.status_label = QLabel(f"Downloading {release.filename}…")
        layout.addWidget(self.status_label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        self._worker = UpdateDownloadWorker(release, github_token=self._github_token)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, current: int, total: int) -> None:
        if total > 0:
            self.progress.setRange(0, total)
            self.progress.setValue(min(current, total))
            mb_done = current / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            self.status_label.setText(
                f"Downloading {self.release.filename}… ({mb_done:.1f} / {mb_total:.1f} MB)"
            )
        else:
            self.progress.setRange(0, 0)

    def _on_finished(self, package_path: str) -> None:
        from core.update_installer import apply_update
        from pathlib import Path

        try:
            apply_update(Path(package_path), self.release)
        except UpdateInstallError as e:
            QMessageBox.critical(self, "Update failed", str(e))
            self.reject()
            return

        QMessageBox.information(
            self,
            "Update",
            "The update will finish after the application closes.\n"
            "Please wait for the installer or updater to complete.",
        )
        self.accept()
        qapp = QApplication.instance()
        if qapp is not None:
            qapp.quit()
        else:
            sys.exit(0)

    def _on_error(self, message: str) -> None:
        QMessageBox.critical(self, "Update failed", message)
        self.reject()


class UpdateController:
    """Coordinates background check, prompts, and manual update from the main window."""

    def __init__(self, main_window, app_config) -> None:
        self._window = main_window
        self._config = app_config
        self._check_worker: UpdateCheckWorker | None = None

    def _repo(self) -> str:
        return str(
            self._config.get("update", "github_repo", default="HFDWKJ/MediaManager")
        ).strip() or "HFDWKJ/MediaManager"

    def _github_token(self) -> str:
        from core.update_checker import resolve_github_token

        configured = str(self._config.get("update", "github_token", default="") or "")
        return resolve_github_token(configured)

    def check_on_startup_enabled(self) -> bool:
        return bool(self._config.get("update", "check_on_startup", default=True))

    def schedule_startup_check(self, delay_ms: int = 2000) -> None:
        if not self.check_on_startup_enabled():
            return
        from PyQt6.QtCore import QTimer

        QTimer.singleShot(delay_ms, self._startup_check)

    def _dismissed_version(self) -> str:
        return str(self._config.get("update", "dismissed_version", default="") or "").strip()

    def _set_dismissed_version(self, version: str) -> None:
        if "update" not in self._config.raw or not isinstance(self._config.raw["update"], dict):
            self._config.raw["update"] = {}
        self._config.raw["update"]["dismissed_version"] = version
        from utils.config import save_config

        save_config(self._config)

    def check_for_updates_manual(self) -> None:
        self._run_check(on_startup=False)

    def _startup_check(self) -> None:
        self._run_check(on_startup=True)

    def _run_check(self, *, on_startup: bool) -> None:
        if self._check_worker is not None and self._check_worker.isRunning():
            return
        self._check_worker = UpdateCheckWorker(
            self._repo(),
            github_token=self._github_token(),
        )
        self._check_worker.finished_ok.connect(
            lambda release: self._on_check_done(release, on_startup=on_startup)
        )
        self._check_worker.error.connect(
            lambda msg: self._on_check_error(msg, on_startup=on_startup)
        )
        self._check_worker.start()
        if not on_startup:
            self._window.statusBar().showMessage("Checking for updates…", 5000)

    def _on_check_error(self, message: str, *, on_startup: bool) -> None:
        self._window.statusBar().clearMessage()
        if on_startup:
            return
        QMessageBox.warning(
            self._window,
            "Update check",
            f"Could not check for updates.\n\n{message}",
        )

    def _on_check_done(self, release: ReleaseAsset | None, *, on_startup: bool) -> None:
        self._window.statusBar().clearMessage()
        if release is None:
            if not on_startup:
                QMessageBox.information(
                    self._window,
                    "Update check",
                    f"You are running the latest version ({__version__}).",
                )
            return

        if on_startup and release.version == self._dismissed_version():
            return

        dlg = UpdateAvailableDialog(release, repo=self._repo(), parent=self._window)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            if dlg.dismissed_later():
                self._set_dismissed_version(release.version)
            return

        if not dlg.wants_update():
            return

        if not can_apply_in_app_update():
            return

        progress = UpdateProgressDialog(
            release,
            github_token=self._github_token(),
            parent=self._window,
        )
        progress.exec()
