"""DiskGenius-style main toolbar (single row of large actions)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QHBoxLayout, QToolButton, QWidget


@dataclass
class ToolbarAction:
    label: str
    icon: str
    slot: Callable[[], None]
    tooltip: str = ""
    checkable: bool = False


class DiskGeniusToolbar(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dgToolbar")
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(6, 4, 6, 4)
        self._layout.setSpacing(4)
        self._buttons: list[QToolButton] = []
        self._online_btn: QToolButton | None = None

    def add_actions(self, actions: list[ToolbarAction]) -> None:
        for spec in actions:
            btn = QToolButton()
            btn.setText(f"{spec.icon}\n{spec.label}")
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            btn.setToolTip(spec.tooltip or spec.label)
            btn.setFixedSize(72, 64)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if spec.checkable:
                btn.setCheckable(True)
                if "online" in spec.label.lower():
                    self._online_btn = btn
            if spec.checkable:
                btn.toggled.connect(spec.slot)  # type: ignore[arg-type]
            else:
                btn.clicked.connect(spec.slot)
            self._layout.addWidget(btn)
            self._buttons.append(btn)
        self._layout.addStretch()

    def online_only_button(self) -> QToolButton | None:
        return self._online_btn

    @staticmethod
    def stylesheet(theme: str = "dark") -> str:
        from gui.dg_theme import toolbar_stylesheet

        return toolbar_stylesheet(theme)
