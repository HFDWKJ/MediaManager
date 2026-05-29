"""Filter controls above the folder tree."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class TreeFilterBar(QWidget):
    """Summary line and view filters for the center panel."""

    online_only_changed = pyqtSignal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("treeFilterBar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 6)
        layout.setSpacing(12)

        self.summary = QLabel("Folder tree")
        self.summary.setObjectName("treeSummary")
        layout.addWidget(self.summary, 1)

        self.online_btn = QPushButton("Online only: Off")
        self.online_btn.setCheckable(True)
        self.online_btn.setToolTip("Hide folders on offline or missing devices")
        self.online_btn.toggled.connect(self._on_online_toggled)
        layout.addWidget(self.online_btn)

    def _on_online_toggled(self, checked: bool) -> None:
        self.online_btn.setText(f"Online only: {'On' if checked else 'Off'}")
        self.online_only_changed.emit(checked)

    def set_summary(self, text: str) -> None:
        self.summary.setText(text)

    def online_only(self) -> bool:
        return self.online_btn.isChecked()

    @staticmethod
    def stylesheet(theme: str = "dark") -> str:
        from gui.dg_theme import filter_bar_stylesheet

        return filter_bar_stylesheet(theme)
