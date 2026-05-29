"""Office-style ribbon toolbar (tabs + grouped buttons, collapsible) — dark theme."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QTabWidget,
    QToolButton, QVBoxLayout, QWidget,
)


@dataclass
class RibbonAction:
    label: str
    icon: str
    slot: Callable[..., object]
    tooltip: str = ""
    large: bool = True
    primary: bool = False
    danger: bool = False
    checkable: bool = False


class _RibbonGroup(QFrame):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ribbonGroup")
        self.setFrameShape(QFrame.Shape.NoFrame)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 10, 2)
        layout.setSpacing(2)

        self._buttons = QHBoxLayout()
        self._buttons.setSpacing(6)
        layout.addLayout(self._buttons)

        caption = QLabel(title)
        caption.setObjectName("ribbonGroupTitle")
        caption.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(caption)

    def add_action(self, spec: RibbonAction) -> QToolButton:
        btn = QToolButton()
        btn.setText(f"{spec.icon}\n{spec.label}" if spec.large else f"{spec.icon} {spec.label}")
        if spec.large:
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            btn.setFixedSize(76, 70)
        else:
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            btn.setMinimumHeight(30)
        if spec.tooltip:
            btn.setToolTip(spec.tooltip)
        if spec.primary:
            btn.setObjectName("ribbonPrimary")
        if spec.danger:
            btn.setObjectName("ribbonDanger")
        if spec.checkable:
            btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if spec.checkable:
            btn.toggled.connect(spec.slot)  # type: ignore[arg-type]
        else:
            btn.clicked.connect(spec.slot)
        self._buttons.addWidget(btn)
        return btn


class OfficeRibbon(QWidget):
    """Ribbon with dark styling matching the rest of the app."""

    collapsed_changed = pyqtSignal(bool)

    RIBBON_BODY_HEIGHT = 84

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("officeRibbon")
        self._collapsed = False
        self._online_btn: QToolButton | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QWidget()
        header.setObjectName("ribbonHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 6, 0)
        header_layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("ribbonTabs")
        self.tabs.setDocumentMode(True)
        self.tabs.tabBar().setExpanding(False)
        header_layout.addWidget(self.tabs, 1)

        self.collapse_btn = QToolButton()
        self.collapse_btn.setObjectName("ribbonCollapse")
        self.collapse_btn.setText("▲")
        self.collapse_btn.setToolTip("Collapse ribbon (Ctrl+F1)")
        self.collapse_btn.setFixedSize(32, 28)
        self.collapse_btn.clicked.connect(self.toggle_collapsed)
        header_layout.addWidget(self.collapse_btn)

        root.addWidget(header)

    def add_tab(self, name: str, groups: list[tuple[str, list[RibbonAction]]]) -> None:
        page = QWidget()
        page.setObjectName("ribbonPage")
        page.setMinimumHeight(self.RIBBON_BODY_HEIGHT)

        scroll = QScrollArea()
        scroll.setObjectName("ribbonScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMinimumHeight(self.RIBBON_BODY_HEIGHT)
        scroll.setMaximumHeight(self.RIBBON_BODY_HEIGHT)

        inner = QWidget()
        inner.setObjectName("ribbonInner")
        row = QHBoxLayout(inner)
        row.setContentsMargins(8, 4, 8, 4)
        row.setSpacing(0)
        row.setAlignment(Qt.AlignmentFlag.AlignLeft)

        for i, (group_title, actions) in enumerate(groups):
            if i > 0:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.VLine)
                sep.setObjectName("ribbonSeparator")
                sep.setFixedWidth(1)
                row.addWidget(sep)
            grp = _RibbonGroup(group_title)
            for act in actions:
                btn = grp.add_action(act)
                if act.checkable and "online" in act.label.lower():
                    self._online_btn = btn
            row.addWidget(grp)

        row.addStretch()
        scroll.setWidget(inner)

        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)

        self.tabs.addTab(page, name)

    def online_only_button(self) -> QToolButton | None:
        return self._online_btn

    def toggle_collapsed(self) -> None:
        self.set_collapsed(not self._collapsed)

    def set_collapsed(self, collapsed: bool) -> None:
        if self._collapsed == collapsed:
            return
        self._collapsed = collapsed
        for i in range(self.tabs.count()):
            page = self.tabs.widget(i)
            if page:
                page.setVisible(not collapsed)
        self.collapse_btn.setText("▼" if collapsed else "▲")
        self.collapse_btn.setToolTip(
            "Expand ribbon (Ctrl+F1)" if collapsed else "Collapse ribbon (Ctrl+F1)"
        )
        h = 34 if collapsed else 34 + self.RIBBON_BODY_HEIGHT
        self.setMinimumHeight(h)
        self.setMaximumHeight(h)
        self.collapsed_changed.emit(collapsed)

    def is_collapsed(self) -> bool:
        return self._collapsed

    @staticmethod
    def stylesheet() -> str:
        bg = "#2d2d30"
        bg_panel = "#252526"
        bg_hover = "#3e3e42"
        border = "#3f3f46"
        text = "#e0e0e0"
        text_dim = "#9d9d9d"
        accent = "#0078d4"
        accent_hover = "#1a8ae6"
        return f"""
        #officeRibbon, #ribbonHeader, #ribbonPage, #ribbonGroup,
        #ribbonScroll, #ribbonInner {{
            background-color: {bg};
            color: {text};
        }}
        #ribbonTabs {{
            background-color: {bg_panel};
        }}
        #ribbonTabs::pane {{
            background-color: {bg};
            border: none;
            top: 0px;
        }}
        #ribbonTabs QTabBar {{
            background-color: {bg_panel};
        }}
        #ribbonTabs QTabBar::tab {{
            background-color: {bg_panel};
            color: {text_dim};
            padding: 8px 18px;
            margin-right: 1px;
            border: none;
            border-bottom: 2px solid transparent;
            min-width: 64px;
        }}
        #ribbonTabs QTabBar::tab:selected {{
            background-color: {bg};
            color: {text};
            font-weight: 600;
            border-bottom: 2px solid {accent};
        }}
        #ribbonTabs QTabBar::tab:hover:!selected {{
            background-color: {bg_hover};
            color: {text};
        }}
        #ribbonGroupTitle {{
            color: {text_dim};
            font-size: 11px;
        }}
        #ribbonSeparator {{
            background-color: {border};
            margin: 8px 6px;
        }}
        #ribbonCollapse {{
            background-color: {bg_hover};
            border: 1px solid {border};
            color: {text};
            border-radius: 3px;
        }}
        #ribbonCollapse:hover {{
            background-color: #4a4a4f;
            border-color: {accent};
        }}
        #officeRibbon QToolButton {{
            background-color: {bg_hover};
            color: {text};
            border: 1px solid {border};
            border-radius: 4px;
            padding: 4px;
            font-size: 11px;
        }}
        #officeRibbon QToolButton:hover {{
            background-color: #4a4a4f;
            border-color: {accent};
        }}
        #officeRibbon QToolButton:pressed {{
            background-color: #094771;
            border-color: {accent};
        }}
        #officeRibbon QToolButton:checked {{
            background-color: #094771;
            border-color: {accent};
            color: #ffffff;
        }}
        #officeRibbon QToolButton#ribbonPrimary {{
            background-color: #0e639c;
            border-color: {accent};
        }}
        #officeRibbon QToolButton#ribbonPrimary:hover {{
            background-color: {accent_hover};
        }}
        #officeRibbon QToolButton#ribbonDanger {{
            color: #f48771;
            background-color: #3c2a2a;
            border-color: #6b3a3a;
        }}
        #officeRibbon QToolButton#ribbonDanger:hover {{
            background-color: #4a3232;
            border-color: #f48771;
        }}
        QScrollBar:horizontal {{
            background: {bg_panel};
            height: 8px;
        }}
        QScrollBar::handle:horizontal {{
            background: {border};
            border-radius: 4px;
            min-width: 24px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: #5a5a5e;
        }}
        """
