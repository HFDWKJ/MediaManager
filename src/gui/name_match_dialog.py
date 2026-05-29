"""Review pending name matches."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QVBoxLayout,
)

from core.database import Database
from core.names import format_display_name
from gui.workers import HashVerifyWorker


class NameMatchDialog(QDialog):
    def __init__(self, db: Database, parent=None) -> None:
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Review Name Matches")
        self.resize(700, 450)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Pending groups (exact / similar folder names):"))
        self.groups = QListWidget()
        layout.addWidget(self.groups)

        self.members_label = QLabel("")
        self.members_label.setWordWrap(True)
        layout.addWidget(self.members_label)

        btn_row = QHBoxLayout()
        self.dismiss_btn = QPushButton("Dismiss")
        self.different_btn = QPushButton("Different Item")
        self.hash_btn = QPushButton("Verify with Hash")
        self.close_btn = QPushButton("Close")
        btn_row.addWidget(self.dismiss_btn)
        btn_row.addWidget(self.different_btn)
        btn_row.addWidget(self.hash_btn)
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)

        self.dismiss_btn.clicked.connect(lambda: self._review("dismissed"))
        self.different_btn.clicked.connect(lambda: self._review("confirmed_different"))
        self.hash_btn.clicked.connect(self._verify_hash)
        self.close_btn.clicked.connect(self.accept)
        self.groups.currentRowChanged.connect(self._show_members)

        self._worker: HashVerifyWorker | None = None
        self.refresh()

    def refresh(self) -> None:
        self.groups.clear()
        for g in self.db.get_pending_name_match_groups():
            icon = "🟡" if g["match_type"] == "exact" else "🟠"
            score = f" ({g['similarity_score']:.0%})" if g["similarity_score"] else ""
            item = QListWidgetItem(
                f"{icon} {g['normalized_name']} — {g['member_count']} folders{score}"
            )
            item.setData(Qt.ItemDataRole.UserRole, int(g["id"]))
            self.groups.addItem(item)
        if self.groups.count():
            self.groups.setCurrentRow(0)

    def _current_group_id(self) -> int | None:
        item = self.groups.currentItem()
        return int(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def _show_members(self) -> None:
        gid = self._current_group_id()
        if not gid:
            self.members_label.setText("")
            return
        members = self.db.get_name_match_members(gid)
        lines = [
            f"• {format_display_name(m.original_name)} — {m.device_name} — {m.root_path}\\{m.folder_path}"
            for m in members
        ]
        self.members_label.setText("\n".join(lines))

    def _review(self, status: str) -> None:
        gid = self._current_group_id()
        if gid is None:
            return
        self.db.update_name_match_review(gid, status)
        self.refresh()
        if self.parent() and hasattr(self.parent(), "reload_extractions"):
            self.parent().reload_extractions()

    def _verify_hash(self) -> None:
        gid = self._current_group_id()
        if gid is None:
            return
        members = self.db.get_name_match_members(gid)
        ids = [m.id for m in members]
        self.hash_btn.setEnabled(False)
        self._worker = HashVerifyWorker(self.db, ids)
        self._worker.finished_ok.connect(self._on_hash_done)
        self._worker.error.connect(self._on_hash_error)
        self._worker.start()

    def _on_hash_done(self, result) -> None:
        self.hash_btn.setEnabled(True)
        if gid := self._current_group_id():
            self.db.update_name_match_review(gid, "sent_to_hash")
        QMessageBox.information(self, "Hash Verify", f"{result.status}: {result.message}")
        self.refresh()
        if self.parent() and hasattr(self.parent(), "reload_extractions"):
            self.parent().reload_extractions()

    def _on_hash_error(self, msg: str) -> None:
        self.hash_btn.setEnabled(True)
        QMessageBox.warning(self, "Error", msg)
