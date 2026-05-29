"""Database panel: table view of catalog extraction folders."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QLabel, QMenu, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from core.database import Database, ExtractionRow, FOLDER_TYPE_LABELS
from core.names import format_display_name


class DatabaseTablePanel(QWidget):
    """Tabular view of folders stored in the SQLite catalog."""

    extraction_selected = pyqtSignal(object)  # ExtractionRow | None
    open_in_explorer = pyqtSignal(object)  # ExtractionRow
    delete_requested = pyqtSignal(int)  # extraction id

    def __init__(self, db: Database, parent=None) -> None:
        super().__init__(parent)
        self.db = db
        self._rows: list[ExtractionRow] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.setObjectName("dgCenterPanel")

        heading = QLabel("Catalog — indexed folders")
        heading.setObjectName("dgPanelTitle")
        layout.addWidget(heading)
        row_actions = QHBoxLayout()
        hint = QLabel("Click a row for properties on the right")
        hint.setObjectName("dgPanelHint")
        row_actions.addWidget(hint)
        row_actions.addStretch()
        self.delete_btn = QPushButton("Delete selected")
        self.delete_btn.setObjectName("actionDanger")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._delete_selected)
        row_actions.addWidget(self.delete_btn)
        layout.addLayout(row_actions)

        self.table = QTableWidget(0, 8)
        self.table.setObjectName("dgCatalogTable")
        self.table.setHorizontalHeaderLabels(
            ["Name", "Type", "Device", "Library", "Path", "Files", "Size (MB)", "Status"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._on_selection)
        self.table.cellDoubleClicked.connect(self._on_double_click)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._context_menu)
        layout.addWidget(self.table, 1)

    def load_rows(self, rows: list[ExtractionRow]) -> None:
        self._rows = rows
        sorting = self.table.isSortingEnabled()
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        status_map = {
            "online": "Online",
            "offline": "Offline",
            "missing": "Missing",
        }
        for r, row in enumerate(rows):
            name_item = QTableWidgetItem(format_display_name(row.original_name))
            name_item.setData(Qt.ItemDataRole.UserRole, row.id)
            self.table.setItem(r, 0, name_item)
            self.table.setItem(r, 1, QTableWidgetItem(FOLDER_TYPE_LABELS.get(row.folder_type, row.folder_type)))
            self.table.setItem(r, 2, QTableWidgetItem(row.device_name))
            self.table.setItem(r, 3, QTableWidgetItem(row.root_label or "—"))
            self.table.setItem(r, 4, QTableWidgetItem(row.folder_path))
            files_item = QTableWidgetItem()
            files_item.setData(Qt.ItemDataRole.DisplayRole, row.file_count)
            self.table.setItem(r, 5, files_item)
            size_item = QTableWidgetItem()
            size_item.setData(Qt.ItemDataRole.DisplayRole, round(row.total_size / 1024 / 1024, 1))
            self.table.setItem(r, 6, size_item)
            self.table.setItem(r, 7, QTableWidgetItem(status_map.get(row.availability, row.availability)))
        self.table.resizeColumnsToContents()
        self.table.setSortingEnabled(sorting)

    def select_extraction_id(self, extraction_id: int) -> None:
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == extraction_id:
                self.table.selectRow(r)
                self.table.scrollToItem(item)
                return

    def _row_at(self, table_row: int) -> ExtractionRow | None:
        item = self.table.item(table_row, 0)
        if not item:
            return None
        eid = item.data(Qt.ItemDataRole.UserRole)
        for row in self._rows:
            if row.id == eid:
                return row
        return None

    def _on_selection(self) -> None:
        selected = self.table.selectedItems()
        if not selected:
            self.delete_btn.setEnabled(False)
            self.extraction_selected.emit(None)
            return
        row = self._row_at(selected[0].row())
        self.delete_btn.setEnabled(row is not None)
        self.extraction_selected.emit(row)

    def _delete_selected(self) -> None:
        eid = self.current_extraction_id()
        if eid is not None:
            self.delete_requested.emit(eid)

    def _on_double_click(self, row: int, _col: int) -> None:
        ext = self._row_at(row)
        if ext:
            self.open_in_explorer.emit(ext)

    def _context_menu(self, pos) -> None:
        selected = self.table.selectedItems()
        if not selected:
            return
        ext = self._row_at(selected[0].row())
        if not ext:
            return
        menu = QMenu(self)
        explore = QAction("Show in Explorer", self)
        explore.triggered.connect(lambda: self.open_in_explorer.emit(ext))
        menu.addAction(explore)
        menu.addSeparator()
        delete_act = QAction("Delete this record…", self)
        delete_act.triggered.connect(lambda: self.delete_requested.emit(ext.id))
        menu.addAction(delete_act)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def current_extraction_id(self) -> int | None:
        selected = self.table.selectedItems()
        if not selected:
            return None
        ext = self._row_at(selected[0].row())
        return ext.id if ext else None
