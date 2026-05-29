"""Approve folders before adding to the database."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from core.database import FOLDER_TYPE_LABELS
from core.folder_preview import FolderPreview


class ApproveFoldersDialog(QDialog):
    def __init__(self, previews: list[FolderPreview], title: str = "Approve folders", parent=None) -> None:
        super().__init__(parent)
        self.previews = previews
        self.approved: list[FolderPreview] = []
        self.setWindowTitle(title)
        self.resize(900, 420)

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                "Review folders found on disk. Uncheck any you do not want in the catalog. "
                "Nothing is saved until you click <b>Approve Selected</b>.<br>"
                "All folders default to <i>Collections</i>. Change type to "
                "<i>Root</i> in the detail panel after import if needed."
            )
        )

        self.table = QTableWidget(len(previews), 7)
        self.table.setHorizontalHeaderLabels(
            ["Add", "Name", "Type", "Files", "Size (MB)", "Path", "Status"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 40)

        for row, p in enumerate(previews):
            check = QTableWidgetItem()
            check.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            check.setCheckState(Qt.CheckState.Checked)
            self.table.setItem(row, 0, check)
            self.table.setItem(row, 1, QTableWidgetItem(p.display_name))
            self.table.setItem(row, 2, QTableWidgetItem(FOLDER_TYPE_LABELS.get(p.folder_type, "")))
            self.table.setItem(row, 3, QTableWidgetItem(str(p.file_count)))
            self.table.setItem(row, 4, QTableWidgetItem(f"{p.size_mb:.1f}"))
            self.table.setItem(row, 5, QTableWidgetItem(p.display_path))
            status = "New" if p.is_new else "Update existing"
            self.table.setItem(row, 6, QTableWidgetItem(status))

        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        select_all = QPushButton("Select All")
        select_none = QPushButton("Select None")
        approve_btn = QPushButton("Approve Selected")
        cancel_btn = QPushButton("Cancel")
        btn_row.addWidget(select_all)
        btn_row.addWidget(select_none)
        btn_row.addStretch()
        btn_row.addWidget(approve_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        select_all.clicked.connect(self._select_all)
        select_none.clicked.connect(self._select_none)
        approve_btn.clicked.connect(self._approve)
        cancel_btn.clicked.connect(self.reject)

    def _select_all(self) -> None:
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)

    def _select_none(self) -> None:
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)

    def _approve(self) -> None:
        selected: list[FolderPreview] = []
        for row, preview in enumerate(self.previews):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                selected.append(preview)
        if not selected:
            QMessageBox.information(self, "Approve", "No folders selected.")
            return
        self.approved = selected
        self.accept()
