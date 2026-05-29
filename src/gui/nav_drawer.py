"""Collapsible side navigation drawer for grouped actions."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from gui.action_bar import ActionSpec


class NavDrawer(QWidget):
    """Slide-out menu panel; toggle width between 0 and expanded."""

    toggled = pyqtSignal(bool)

    EXPANDED_WIDTH = 232

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._expanded = True
        self.setObjectName("navDrawer")
        self.setFixedWidth(self.EXPANDED_WIDTH)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(12, 10, 8, 6)
        title = QPushButton("✕  Close menu")
        title.setFlat(True)
        title.setObjectName("navDrawerClose")
        title.clicked.connect(lambda: self.set_expanded(False))
        header_layout.addWidget(title)
        outer.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        body = QWidget()
        self._body_layout = QVBoxLayout(body)
        self._body_layout.setContentsMargins(8, 0, 8, 12)
        self._body_layout.setSpacing(14)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

    def add_group(self, title: str, actions: list[ActionSpec]) -> None:
        group = QWidget()
        col = QVBoxLayout(group)
        col.setContentsMargins(4, 0, 4, 0)
        col.setSpacing(4)

        heading = QPushButton(title.upper())
        heading.setEnabled(False)
        heading.setFlat(True)
        heading.setObjectName("navGroupTitle")
        col.addWidget(heading)

        for spec in actions:
            btn = QPushButton(spec.label)
            if spec.tooltip:
                btn.setToolTip(spec.tooltip)
            if spec.primary:
                btn.setObjectName("actionPrimary")
            if spec.danger:
                btn.setObjectName("actionDanger")
            if spec.checkable:
                btn.setCheckable(True)
            btn.clicked.connect(spec.slot)
            col.addWidget(btn)

        self._body_layout.addWidget(group)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setObjectName("navSeparator")
        self._body_layout.addWidget(line)

    def set_expanded(self, expanded: bool) -> None:
        if self._expanded == expanded:
            return
        self._expanded = expanded
        self.setFixedWidth(self.EXPANDED_WIDTH if expanded else 0)
        self.setVisible(expanded)
        self.toggled.emit(expanded)

    def is_expanded(self) -> bool:
        return self._expanded

    def toggle(self) -> None:
        self.set_expanded(not self._expanded)

    @staticmethod
    def stylesheet() -> str:
        return """
        #navDrawer {
            background-color: #252526;
            border-right: 1px solid #3e3e42;
        }
        #navDrawerClose {
            text-align: left;
            color: #cccccc;
            font-weight: 600;
        }
        #navGroupTitle {
            color: #858585;
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 0.6px;
        }
        #navDrawer QPushButton:enabled {
            min-height: 28px;
            padding: 4px 10px;
            border: 1px solid #555558;
            border-radius: 4px;
            background-color: #3c3c3c;
            text-align: left;
        }
        #navDrawer QPushButton:enabled:hover {
            background-color: #4a4a4d;
        }
        #navDrawer QPushButton#actionPrimary {
            background-color: #0e639c;
            border-color: #1177bb;
            font-weight: 600;
        }
        #navDrawer QPushButton#actionDanger {
            color: #f48771;
            border-color: #6b3a3a;
            background-color: #3c2f2f;
        }
        #navSeparator {
            color: #3e3e42;
            max-height: 1px;
        }
        """
