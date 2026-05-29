"""Grouped toolbar for main window actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


@dataclass
class ActionSpec:
    label: str
    slot: Callable[[], None]
    tooltip: str = ""
    primary: bool = False
    danger: bool = False
    checkable: bool = False


class ActionBar(QWidget):
    """Horizontal bar with labeled button groups separated by dividers."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("actionBar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(0)

        self._groups = QHBoxLayout()
        self._groups.setSpacing(18)
        layout.addLayout(self._groups)
        layout.addStretch()

        self._buttons: list[QPushButton] = []

    def add_group(self, title: str, actions: list[ActionSpec]) -> None:
        group = QWidget()
        group.setObjectName("actionGroup")
        col = QVBoxLayout(group)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(4)

        heading = QLabel(title.upper())
        heading.setObjectName("actionGroupTitle")
        col.addWidget(heading)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        for spec in actions:
            btn = QPushButton(spec.label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if spec.tooltip:
                btn.setToolTip(spec.tooltip)
            if spec.primary:
                btn.setObjectName("actionPrimary")
            if spec.danger:
                btn.setObjectName("actionDanger")
            if spec.checkable:
                btn.setCheckable(True)
            btn.clicked.connect(spec.slot)
            row.addWidget(btn)
            self._buttons.append(btn)

        col.addLayout(row)
        self._groups.addWidget(group)

    def add_separator(self) -> None:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setObjectName("actionSeparator")
        line.setFixedWidth(1)
        self._groups.addWidget(line)

    @staticmethod
    def stylesheet() -> str:
        return """
        #actionBar {
            background-color: #252526;
            border-bottom: 1px solid #3e3e42;
        }
        #actionGroupTitle {
            color: #858585;
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 0.6px;
        }
        #actionBar QPushButton {
            min-height: 26px;
            padding: 4px 12px;
            border: 1px solid #555558;
            border-radius: 4px;
            background-color: #3c3c3c;
        }
        #actionBar QPushButton:hover {
            background-color: #4a4a4d;
            border-color: #6a6a6e;
        }
        #actionBar QPushButton:pressed {
            background-color: #2a2a2c;
        }
        #actionBar QPushButton:checked {
            background-color: #094771;
            border-color: #0078d4;
        }
        #actionBar QPushButton#actionPrimary {
            background-color: #0e639c;
            border-color: #1177bb;
            font-weight: 600;
        }
        #actionBar QPushButton#actionPrimary:hover {
            background-color: #1177bb;
        }
        #actionBar QPushButton#actionDanger {
            color: #f48771;
            border-color: #6b3a3a;
            background-color: #3c2f2f;
        }
        #actionBar QPushButton#actionDanger:hover {
            background-color: #4a3535;
        }
        #actionSeparator {
            background-color: #3e3e42;
            margin: 4px 0;
            max-width: 1px;
        }
        """
