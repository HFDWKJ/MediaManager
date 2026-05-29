"""Manage Face_UID records — unique 5-character IDs."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from core.database import Database, FaceUidRow
from core.face_uid import UID_LENGTH, generate_unique_uid


class FaceUidDialog(QDialog):
    def __init__(self, db: Database, parent=None) -> None:
        super().__init__(parent)
        self.db = db
        self._selected_id: int | None = None
        self._all_rows: list[FaceUidRow] = []
        self.setWindowTitle("Face UID Manager")
        self.resize(820, 520)

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                f"Generate unique {UID_LENGTH}-character UIDs (A–Z, 0–9). "
                "Each UID is stored once in the database."
            )
        )

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(
            "Filter by UID, nick name, region, comments, or created date…"
        )
        self.search_edit.setClearButtonEnabled(True)
        search_row.addWidget(self.search_edit, 1)
        self.result_label = QLabel()
        self.result_label.setObjectName("dgPanelHint")
        search_row.addWidget(self.result_label)
        layout.addLayout(search_row)

        self.table = QTableWidget(0, 5)
        self.table.setObjectName("dgCatalogTable")
        self.table.setHorizontalHeaderLabels(
            ["UID", "Nick Name", "Region", "Comments", "Created"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSortIndicatorShown(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_selection)
        layout.addWidget(self.table, 1)

        form = QFormLayout()
        self.uid_edit = QLineEdit()
        self.uid_edit.setReadOnly(True)
        self.uid_edit.setPlaceholderText("Click Generate new UID")
        self.nick_edit = QLineEdit()
        self.region_edit = QLineEdit()
        self.comments_edit = QTextEdit()
        self.comments_edit.setMaximumHeight(72)
        form.addRow("UID:", self.uid_edit)
        form.addRow("Nick Name:", self.nick_edit)
        form.addRow("Region:", self.region_edit)
        form.addRow("Comments:", self.comments_edit)
        layout.addLayout(form)

        row1 = QHBoxLayout()
        self.generate_btn = QPushButton("Generate new UID")
        self.generate_btn.setObjectName("actionPrimary")
        self.save_new_btn = QPushButton("Save as new")
        self.update_btn = QPushButton("Update selected")
        self.delete_btn = QPushButton("Delete selected")
        self.delete_btn.setObjectName("actionDanger")
        self.copy_btn = QPushButton("Copy UID")
        row1.addWidget(self.generate_btn)
        row1.addWidget(self.save_new_btn)
        row1.addWidget(self.update_btn)
        row1.addWidget(self.delete_btn)
        row1.addWidget(self.copy_btn)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        row2.addWidget(close_btn)
        layout.addLayout(row2)

        self.generate_btn.clicked.connect(self._generate_uid)
        self.save_new_btn.clicked.connect(self._save_new)
        self.update_btn.clicked.connect(self._update_selected)
        self.delete_btn.clicked.connect(self._delete_selected)
        self.copy_btn.clicked.connect(self._copy_uid)
        self.nick_edit.editingFinished.connect(self._on_nick_editing_finished)
        self.search_edit.textChanged.connect(self._on_search_changed)

        self.refresh()

    def refresh(self, *, select_id: int | None = None) -> None:
        self._all_rows = self.db.list_face_uids()
        self._rebuild_table(select_id=select_id)

    def _on_search_changed(self, _text: str) -> None:
        keep_id = self._selected_id
        self._rebuild_table(select_id=keep_id)

    def _filtered_rows(self) -> list[FaceUidRow]:
        query = self.search_edit.text().strip().casefold()
        if not query:
            return list(self._all_rows)
        matched: list[FaceUidRow] = []
        for row in self._all_rows:
            haystack = " ".join(
                (
                    row.uid,
                    row.nick_name,
                    row.region,
                    row.comments,
                    row.created_at,
                    self._format_created(row.created_at),
                )
            ).casefold()
            if query in haystack:
                matched.append(row)
        return matched

    @staticmethod
    def _format_created(created_at: str) -> str:
        return created_at[:19].replace("T", " ") if created_at else ""

    def _rebuild_table(self, *, select_id: int | None = None) -> None:
        rows = self._filtered_rows()
        total = len(self._all_rows)
        shown = len(rows)
        if total == shown:
            self.result_label.setText(f"{total} record(s)")
        else:
            self.result_label.setText(f"Showing {shown} of {total} record(s)")

        sorting = self.table.isSortingEnabled()
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            uid_item = QTableWidgetItem(row.uid)
            uid_item.setData(Qt.ItemDataRole.UserRole, row.id)
            self.table.setItem(r, 0, uid_item)
            self.table.setItem(r, 1, QTableWidgetItem(row.nick_name))
            self.table.setItem(r, 2, QTableWidgetItem(row.region))
            self.table.setItem(r, 3, QTableWidgetItem(row.comments))
            created = self._format_created(row.created_at)
            created_item = QTableWidgetItem(created)
            created_item.setData(Qt.ItemDataRole.UserRole + 1, row.created_at)
            self.table.setItem(r, 4, created_item)
        self.table.setSortingEnabled(sorting)

        if select_id is not None:
            for r, row in enumerate(rows):
                if row.id == select_id:
                    self._select_table_row(r)
                    return
            self._clear_form()
        elif rows:
            self._select_table_row(0)
        else:
            self._clear_form()

    def _select_table_row(self, row_index: int) -> None:
        if row_index < 0 or row_index >= self.table.rowCount():
            return
        self.table.selectRow(row_index)
        item = self.table.item(row_index, 0)
        if item is not None:
            self.table.scrollToItem(item)
        self._on_selection()

    def _highlight_record_by_id(self, record_id: int) -> None:
        """Select and scroll to a row without loading it into the form."""
        self.table.blockSignals(True)
        try:
            for r in range(self.table.rowCount()):
                item = self.table.item(r, 0)
                if item is None:
                    continue
                rid = item.data(Qt.ItemDataRole.UserRole)
                if rid is not None and int(rid) == record_id:
                    self.table.selectRow(r)
                    self.table.scrollToItem(
                        item, QAbstractItemView.ScrollHint.PositionAtCenter
                    )
                    return
        finally:
            self.table.blockSignals(False)

    def _form_snapshot(self) -> dict[str, str]:
        return {
            "uid": self.uid_edit.text(),
            "nick": self.nick_edit.text(),
            "region": self.region_edit.text(),
            "comments": self.comments_edit.toPlainText(),
        }

    def _apply_form_snapshot(self, snap: dict[str, str]) -> None:
        self.uid_edit.setText(snap["uid"])
        self.nick_edit.setText(snap["nick"])
        self.region_edit.setText(snap["region"])
        self.comments_edit.setPlainText(snap["comments"])

    def _clear_form(self) -> None:
        self._selected_id = None
        self.uid_edit.clear()
        self.nick_edit.clear()
        self.region_edit.clear()
        self.comments_edit.clear()

    def _on_selection(self) -> None:
        items = self.table.selectedItems()
        if not items:
            self._clear_form()
            return
        record_id = items[0].data(Qt.ItemDataRole.UserRole)
        if record_id is None:
            return
        self._selected_id = int(record_id)
        row = self.db.get_face_uid(self._selected_id)
        if not row:
            return
        self.uid_edit.setText(row.uid)
        self.nick_edit.setText(row.nick_name)
        self.region_edit.setText(row.region)
        self.comments_edit.setPlainText(row.comments)

    def _generate_uid(self) -> None:
        try:
            uid = generate_unique_uid(self.db.get_all_face_uid_strings())
        except RuntimeError as e:
            QMessageBox.warning(self, "Face UID", str(e))
            return
        self.uid_edit.setText(uid)
        self._selected_id = None
        self._warn_duplicate_nick_if_needed()

    def _on_nick_editing_finished(self) -> None:
        self._warn_duplicate_nick_if_needed()

    def _warn_duplicate_nick_if_needed(self) -> None:
        nick = self.nick_edit.text().strip()
        if not nick:
            return
        existing = self.db.find_face_uid_by_nick(
            nick, exclude_id=self._selected_id
        )
        if existing is None:
            return
        snap = self._form_snapshot()
        self._highlight_record_by_id(existing.id)
        self._apply_form_snapshot(snap)
        QMessageBox.warning(
            self,
            "Nick Name already exists",
            (
                f"The Nick Name \"{nick}\" is already in the system.\n\n"
                f"UID: {existing.uid}\n"
                f"Nick Name: {existing.nick_name}\n"
                f"Region: {existing.region or '—'}\n"
                f"Comments: {existing.comments or '—'}\n\n"
                f"You can choose to continue adding when you click Save as new."
            ),
        )

    def _confirm_duplicate_nick(self, existing: FaceUidRow, nick: str) -> bool:
        """Show existing record, jump to its row; return True if user continues adding."""
        snap = self._form_snapshot()
        self._highlight_record_by_id(existing.id)
        self._apply_form_snapshot(snap)
        self.raise_()
        self.activateWindow()

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("Nick Name already exists")
        box.setText(f'The Nick Name "{nick}" is already in the system.')
        box.setInformativeText(
            f"Existing record:\n"
            f"UID: {existing.uid}\n"
            f"Nick Name: {existing.nick_name}\n"
            f"Region: {existing.region or '—'}\n"
            f"Comments: {existing.comments or '—'}\n\n"
            f"Continue adding as a new record?"
        )
        continue_btn = box.addButton("Continue adding", QMessageBox.ButtonRole.YesRole)
        cancel_btn = box.addButton("Cancel", QMessageBox.ButtonRole.NoRole)
        box.setDefaultButton(cancel_btn)
        box.exec()
        return box.clickedButton() is continue_btn

    def _save_new(self) -> None:
        snap = self._form_snapshot()
        uid = snap["uid"].strip().upper()
        nick = snap["nick"].strip()
        region = snap["region"]
        comments = snap["comments"]

        if len(uid) != UID_LENGTH:
            QMessageBox.warning(
                self,
                "Face UID",
                f"Click Generate new UID to create a {UID_LENGTH}-character UID first.",
            )
            return

        if nick:
            existing = self.db.find_face_uid_by_nick(nick)
            if existing is not None:
                if not self._confirm_duplicate_nick(existing, nick):
                    return
                snap = self._form_snapshot()
                uid = snap["uid"].strip().upper()
                nick = snap["nick"].strip()
                region = snap["region"]
                comments = snap["comments"]

        if uid in self.db.get_all_face_uid_strings():
            row = self.db.find_face_uid_by_uid(uid)
            if row is not None:
                self._highlight_record_by_id(row.id)
            QMessageBox.warning(
                self,
                "Face UID",
                f"UID {uid} already exists. Generate a new UID before saving.",
            )
            return

        try:
            new_id = self.db.insert_face_uid(uid, nick, region, comments)
        except Exception as e:
            QMessageBox.warning(self, "Face UID", f"Could not save:\n{e}")
            return
        self.refresh(select_id=new_id)
        QMessageBox.information(self, "Face UID", f"Saved UID {uid}.")

    def _update_selected(self) -> None:
        if self._selected_id is None:
            QMessageBox.information(self, "Face UID", "Select a row in the table to update.")
            return
        snap = self._form_snapshot()
        nick = snap["nick"].strip()
        if nick:
            existing = self.db.find_face_uid_by_nick(nick, exclude_id=self._selected_id)
            if existing is not None:
                if not self._confirm_duplicate_nick(existing, nick):
                    return
                snap = self._form_snapshot()
        keep_id = self._selected_id
        self.db.update_face_uid(
            keep_id,
            nick_name=snap["nick"],
            region=snap["region"],
            comments=snap["comments"],
        )
        self.refresh(select_id=keep_id)
        QMessageBox.information(self, "Face UID", "Record updated.")

    def _delete_selected(self) -> None:
        if self._selected_id is None:
            QMessageBox.information(self, "Face UID", "Select a row to delete.")
            return
        uid = self.uid_edit.text()
        reply = QMessageBox.question(
            self,
            "Delete UID",
            f"Delete UID <b>{uid}</b> from the database?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.db.delete_face_uid(self._selected_id)
        self._clear_form()
        self.refresh()

    def _copy_uid(self) -> None:
        uid = self.uid_edit.text().strip()
        if not uid:
            return
        QGuiApplication.clipboard().setText(uid)
