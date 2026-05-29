"""Device and library root list panel."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget, QLabel

from core.database import Database


class DevicePanel(QWidget):
    root_selected = pyqtSignal(int)  # 0 = show all roots
    all_roots_selected = pyqtSignal()

    def __init__(self, db: Database, parent=None) -> None:
        super().__init__(parent)
        self.db = db
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 4, 8)
        heading = QLabel("LIBRARY")
        heading.setStyleSheet("color: #858585; font-size: 10px; font-weight: 600; letter-spacing: 0.6px;")
        layout.addWidget(heading)
        hint = QLabel("Filter the folder tree")
        hint.setStyleSheet("color: #707070; font-size: 11px; margin-bottom: 4px;")
        layout.addWidget(hint)
        self.list = QListWidget()
        self.list.itemClicked.connect(self._on_click)
        layout.addWidget(self.list)

    def refresh(self) -> None:
        self.list.clear()
        all_item = QListWidgetItem("📂 All library roots")
        all_item.setData(256, 0)
        self.list.addItem(all_item)
        for root in self.db.get_roots():
            online = "🟢" if root["is_online"] else "🔴"
            label = root["label"] or root["root_path"]
            text = f"{online} {root['device_name']} — {label}"
            item = QListWidgetItem(text)
            item.setData(256, int(root["id"]))
            self.list.addItem(item)

    def _on_click(self, item: QListWidgetItem) -> None:
        root_id = int(item.data(256) or 0)
        if root_id == 0:
            self.all_roots_selected.emit()
        else:
            self.root_selected.emit(root_id)

    def select_all_roots(self) -> None:
        if self.list.count() > 0:
            self.list.setCurrentRow(0)
