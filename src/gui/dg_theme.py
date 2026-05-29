"""DiskGenius-style themes (light / dark) and application helpers."""

from __future__ import annotations

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

THEME_LIGHT = "light"
THEME_DARK = "dark"

THEME_LABELS = {
    THEME_LIGHT: "Light (classic)",
    THEME_DARK: "Dark (DiskGenius)",
}


def normalize_theme(value: str | None) -> str:
    key = (value or THEME_DARK).strip().lower()
    return key if key in (THEME_LIGHT, THEME_DARK) else THEME_DARK


def toolbar_stylesheet(theme: str) -> str:
    if normalize_theme(theme) == THEME_LIGHT:
        return """
        #dgToolbar {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #f8f8f8, stop:1 #ece9d8);
            border-bottom: 1px solid #aca899;
        }
        #dgToolbar QToolButton {
            background-color: #ece9d8;
            color: #000000;
            border: 1px solid #aca899;
            border-radius: 4px;
            padding: 4px 2px;
            font-size: 11px;
        }
        #dgToolbar QToolButton:hover {
            background-color: #fff8e8;
            border-color: #316ac5;
        }
        #dgToolbar QToolButton:pressed {
            background-color: #c8d8f0;
            border-color: #316ac5;
        }
        #dgToolbar QToolButton:checked {
            background-color: #316ac5;
            color: #ffffff;
            border-color: #316ac5;
        }
        """
    return """
    #dgToolbar {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #3a3a3d, stop:1 #2d2d30);
        border-bottom: 1px solid #1a1a1a;
    }
    #dgToolbar QToolButton {
        background-color: #404045;
        color: #f0f0f0;
        border: 1px solid #55555a;
        border-radius: 4px;
        padding: 4px 2px;
        font-size: 11px;
    }
    #dgToolbar QToolButton:hover {
        background-color: #4d4d52;
        border-color: #6cb6ff;
    }
    #dgToolbar QToolButton:pressed {
        background-color: #2a5a8a;
        border-color: #0078d4;
    }
    #dgToolbar QToolButton:checked {
        background-color: #094771;
        border-color: #0078d4;
    }
    """


def filter_bar_stylesheet(theme: str) -> str:
    if normalize_theme(theme) == THEME_LIGHT:
        return """
        #treeFilterBar { padding: 2px 0; }
        #treeSummary { color: #000000; font-size: 12px; }
        #treeFilterBar QPushButton {
            min-height: 24px;
            padding: 3px 10px;
            border: 1px solid #aca899;
            background-color: #ece9d8;
            font-size: 12px;
            color: #000000;
        }
        #treeFilterBar QPushButton:checked {
            background-color: #316ac5;
            color: #ffffff;
            border-color: #316ac5;
        }
        """
    return """
    #treeFilterBar { padding: 2px 0; }
    #treeSummary { color: #cccccc; font-size: 12px; }
    #treeFilterBar QPushButton {
        min-height: 24px;
        padding: 3px 10px;
        border: 1px solid #555558;
        border-radius: 4px;
        background-color: #333337;
        font-size: 12px;
        color: #e0e0e0;
    }
    #treeFilterBar QPushButton:checked {
        background-color: #094771;
        border-color: #0078d4;
    }
    """


def storage_map_stylesheet(theme: str) -> str:
    if normalize_theme(theme) == THEME_LIGHT:
        return "#storageMapBar { background-color: #f0f0f0; border-bottom: 1px solid #aca899; }"
    return "#storageMapBar { background-color: #1e1e1e; border-bottom: 1px solid #3f3f46; }"


def storage_map_colors(theme: str) -> dict[str, QColor]:
    if normalize_theme(theme) == THEME_LIGHT:
        return {
            "bg": QColor("#f0f0f0"),
            "title": QColor("#404040"),
            "bar": QColor("#ffffff"),
            "bar_border": QColor("#aca899"),
            "empty": QColor("#808080"),
            "seg_border": QColor("#333333"),
            "seg_text": QColor("#000000"),
        }
    return {
        "bg": QColor("#1e1e1e"),
        "title": QColor("#9d9d9d"),
        "bar": QColor("#2d2d30"),
        "bar_border": QColor("#555558"),
        "empty": QColor("#707070"),
        "seg_border": QColor("#1a1a1a"),
        "seg_text": QColor("#ffffff"),
    }


def library_tree_stylesheet(theme: str) -> str:
    """Tree view only — keep out of app-wide stylesheet to avoid paint bugs."""
    if normalize_theme(theme) == THEME_LIGHT:
        return """
        QTreeView#dgDeviceTree {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #aca899;
            font-size: 13px;
            alternate-background-color: #f5f5f5;
            outline: none;
        }
        QTreeView#dgDeviceTree::item {
            padding: 4px 2px;
            color: #000000;
        }
        QTreeView#dgDeviceTree::item:selected {
            background-color: #316ac5;
            color: #ffffff;
        }
        QTreeView#dgDeviceTree::item:hover:!selected {
            background-color: #e8f4ff;
            color: #000000;
        }
        QTreeView#dgDeviceTree::branch {
            background-color: #ffffff;
        }
        """
    return """
    QTreeView#dgDeviceTree {
        background-color: #1e1e1e;
        color: #e0e0e0;
        border: 1px solid #3f3f46;
        font-size: 13px;
        alternate-background-color: #252526;
        outline: none;
    }
    QTreeView#dgDeviceTree::item {
        padding: 4px 2px;
        color: #e0e0e0;
        min-height: 20px;
    }
    QTreeView#dgDeviceTree::item:selected {
        background-color: #094771;
        color: #ffffff;
    }
    QTreeView#dgDeviceTree::item:hover:!selected {
        background-color: #2a2d2e;
        color: #ffffff;
    }
    QTreeView#dgDeviceTree::branch {
        background-color: #1e1e1e;
    }
    """


def menu_bar_stylesheet(theme: str) -> str:
    """Menu bar + dropdown menus (apply only to QMenuBar#appMenuBar, not app-wide)."""
    if normalize_theme(theme) == THEME_LIGHT:
        return """
        QMenuBar#appMenuBar {
            background-color: #f0f0f0;
            color: #000000;
            border-bottom: 1px solid #aca899;
            padding: 2px 4px;
            spacing: 2px;
        }
        QMenuBar#appMenuBar::item {
            background: transparent;
            padding: 4px 10px;
        }
        QMenuBar#appMenuBar::item:selected {
            background-color: #316ac5;
            color: #ffffff;
        }
        QMenu {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #aca899;
        }
        QMenu::item {
            padding: 6px 28px 6px 12px;
        }
        QMenu::item:selected {
            background-color: #316ac5;
            color: #ffffff;
        }
        QMenu::separator {
            height: 1px;
            background: #c0c0c0;
            margin: 4px 8px;
        }
        """
    return """
    QMenuBar#appMenuBar {
        background-color: #2d2d30;
        color: #e0e0e0;
        border-bottom: 1px solid #3f3f46;
        padding: 2px 4px;
        spacing: 2px;
    }
    QMenuBar#appMenuBar::item {
        background: transparent;
        padding: 4px 10px;
    }
    QMenuBar#appMenuBar::item:selected {
        background-color: #094771;
        color: #ffffff;
    }
    QMenu {
        background-color: #2d2d30;
        color: #e0e0e0;
        border: 1px solid #3f3f46;
    }
    QMenu::item {
        padding: 6px 28px 6px 12px;
    }
    QMenu::item:selected {
        background-color: #094771;
        color: #ffffff;
    }
    QMenu::separator {
        height: 1px;
        background: #3f3f46;
        margin: 4px 8px;
    }
    """


def app_stylesheet(theme: str) -> str:
    """Styles for central panels only — not the menu bar (see menu_bar_stylesheet)."""
    t = normalize_theme(theme)
    return filter_bar_stylesheet(t) + storage_map_stylesheet(t) + _shell_stylesheet(t)


def _shell_stylesheet(theme: str) -> str:
    if normalize_theme(theme) == THEME_LIGHT:
        return """
        QWidget#centralShell { background-color: #ece9d8; }
        QStatusBar {
            background-color: #ece9d8;
            color: #000000;
            border-top: 1px solid #aca899;
        }
        QSplitter::handle { background-color: #aca899; width: 3px; }
        QTableWidget#dgCatalogTable {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #aca899;
            gridline-color: #d4d0c8;
            selection-background-color: #316ac5;
            selection-color: #ffffff;
        }
        QHeaderView::section {
            background-color: #ece9d8;
            color: #000000;
            padding: 5px;
            border: 1px solid #aca899;
            font-weight: bold;
        }
        QWidget#dgLeftPanel {
            background-color: #ece9d8;
            border-right: 1px solid #aca899;
        }
        QWidget#dgRightPanel {
            background-color: #ece9d8;
            border-left: 1px solid #aca899;
        }
        QWidget#dgCenterPanel { background-color: #f0f0f0; }
        QLabel#dgPanelTitle {
            color: #000080;
            font-weight: bold;
            font-size: 12px;
        }
        QLabel#dgPanelHint { color: #404040; font-size: 11px; }
        QLineEdit, QComboBox, QTextEdit {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #aca899;
            padding: 3px;
        }
        QComboBox QAbstractItemView {
            background-color: #ffffff;
            color: #000000;
            selection-background-color: #316ac5;
        }
        QPushButton {
            background-color: #ece9d8;
            color: #000000;
            border: 1px solid #aca899;
            padding: 5px 12px;
            min-height: 22px;
        }
        QPushButton:hover { background-color: #fff8e8; border-color: #316ac5; }
        QPushButton#actionPrimary {
            background-color: #316ac5;
            color: #ffffff;
            font-weight: bold;
        }
        QPushButton#actionDanger {
            background-color: #ffeeee;
            color: #8b0000;
            border-color: #cc6666;
        }
        QPushButton:disabled {
            color: #888888;
            background-color: #e0e0e0;
        }
        QScrollArea { background-color: transparent; border: none; }
        QDialog { background-color: #ece9d8; color: #000000; }
        """
    return """
    QWidget#centralShell { background-color: #252526; }
    QStatusBar {
        background-color: #007acc;
        color: #ffffff;
        border-top: 1px solid #3f3f46;
    }
    QSplitter::handle { background-color: #3f3f46; width: 3px; }
    QTableWidget#dgCatalogTable {
        background-color: #1e1e1e;
        color: #e0e0e0;
        border: 1px solid #3f3f46;
        gridline-color: #3f3f46;
        selection-background-color: #094771;
        selection-color: #ffffff;
    }
    QHeaderView::section {
        background-color: #2d2d30;
        color: #cccccc;
        padding: 5px;
        border: 1px solid #3f3f46;
        font-weight: bold;
    }
    QWidget#dgLeftPanel {
        background-color: #252526;
        border-right: 1px solid #3f3f46;
    }
    QWidget#dgRightPanel {
        background-color: #252526;
        border-left: 1px solid #3f3f46;
    }
    QWidget#dgCenterPanel { background-color: #1e1e1e; }
    QLabel#dgPanelTitle {
        color: #6cb6ff;
        font-weight: bold;
        font-size: 12px;
    }
    QLabel#dgPanelHint { color: #9d9d9d; font-size: 11px; }
    QLineEdit, QComboBox, QTextEdit {
        background-color: #3c3c3c;
        color: #e0e0e0;
        border: 1px solid #3f3f46;
        padding: 3px;
    }
    QComboBox QAbstractItemView {
        background-color: #2d2d30;
        color: #e0e0e0;
        selection-background-color: #094771;
    }
    QPushButton {
        background-color: #3c3c3c;
        color: #e0e0e0;
        border: 1px solid #3f3f46;
        padding: 5px 12px;
        min-height: 22px;
    }
    QPushButton:hover {
        background-color: #4a4a4f;
        border-color: #0078d4;
    }
    QPushButton#actionPrimary {
        background-color: #0e639c;
        color: #ffffff;
        font-weight: bold;
        border-color: #0078d4;
    }
    QPushButton#actionDanger {
        color: #f48771;
        background-color: #3c2a2a;
        border-color: #6b3a3a;
    }
    QPushButton:disabled {
        color: #6a6a6a;
        background-color: #2a2a2a;
    }
    QScrollArea { background-color: transparent; border: none; }
    QDialog { background-color: #252526; color: #e0e0e0; }
    """


def apply_palette(app: QApplication, theme: str) -> None:
    t = normalize_theme(theme)
    p = QPalette()
    if t == THEME_LIGHT:
        p.setColor(QPalette.ColorRole.Window, QColor(236, 233, 216))
        p.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        p.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        p.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        p.setColor(QPalette.ColorRole.Button, QColor(236, 233, 216))
        p.setColor(QPalette.ColorRole.Highlight, QColor(49, 106, 197))
    else:
        p.setColor(QPalette.ColorRole.Window, QColor(37, 37, 38))
        p.setColor(QPalette.ColorRole.WindowText, QColor(224, 224, 224))
        p.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
        p.setColor(QPalette.ColorRole.Text, QColor(224, 224, 224))
        p.setColor(QPalette.ColorRole.Button, QColor(60, 60, 60))
        p.setColor(QPalette.ColorRole.Highlight, QColor(9, 71, 113))
    app.setPalette(p)


def apply_theme(app: QApplication, theme: str) -> None:
    """Apply full DiskGenius theme to the application."""
    app.setStyle("Fusion")
    apply_palette(app, theme)
    app.setStyleSheet(app_stylesheet(theme))
