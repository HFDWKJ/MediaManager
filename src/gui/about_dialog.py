"""About dialog — version info and changelog."""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTextBrowser,
    QVBoxLayout,
)

from version import __developer__, __version__
from utils.paths import data_dir, is_portable_mode


def _changelog_path() -> Path | None:
    candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / "CHANGELOG.md")
    repo_root = Path(__file__).resolve().parents[2]
    candidates.append(repo_root / "CHANGELOG.md")
    for path in candidates:
        if path.is_file():
            return path
    return None


def _load_changelog_text() -> str:
    path = _changelog_path()
    if path is None:
        return (
            "# Changelog\n\n"
            "No changelog file found.\n\n"
            "Add `CHANGELOG.md` at the project root to show release notes here."
        )
    try:
        return path.read_text(encoding="utf-8")
    except OSError as e:
        return f"# Changelog\n\nCould not read changelog:\n\n{e}"


class AboutDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("About Media Manager")
        self.setMinimumSize(520, 420)

        layout = QVBoxLayout(self)

        title = QLabel("Media Manager")
        title.setObjectName("aboutTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title.font()
        font.setPointSize(font.pointSize() + 4)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        version = QLabel(f"Version {__version__}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setObjectName("dgPanelHint")
        layout.addWidget(version)

        developer = QLabel(f"Developer: {__developer__}")
        developer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        developer.setObjectName("dgPanelHint")
        layout.addWidget(developer)

        if is_portable_mode():
            edition = QLabel("Portable edition — all data stored locally")
            edition.setAlignment(Qt.AlignmentFlag.AlignCenter)
            edition.setObjectName("dgPanelHint")
            layout.addWidget(edition)

        data_path = QLabel(f"Data folder: {data_dir()}")
        data_path.setAlignment(Qt.AlignmentFlag.AlignCenter)
        data_path.setWordWrap(True)
        data_path.setObjectName("dgPanelHint")
        layout.addWidget(data_path)

        layout.addWidget(QLabel("Changelog"))

        self.changelog_view = QTextBrowser()
        self.changelog_view.setOpenExternalLinks(True)
        self.changelog_view.setMarkdown(_load_changelog_text())
        layout.addWidget(self.changelog_view, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
