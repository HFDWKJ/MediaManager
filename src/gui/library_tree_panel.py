"""Library panel — device / library root / folder tree."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QModelIndex, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QKeySequence, QPalette
from PyQt6.QtWidgets import (
    QLabel,
    QMenu,
    QSizePolicy,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from core.database import Database
from core.device_manager import check_path_accessible
from core.device_types import DEVICE_TYPE_LABELS, DEVICE_TYPE_ORDER
from gui.dg_theme import THEME_DARK, THEME_LIGHT, normalize_theme
from gui.library_tree_model import (
    KIND_ALL,
    KIND_CATEGORY,
    KIND_EMPTY,
    KIND_FOLDER,
    KIND_LIBRARY_ROOT,
    KIND_PLACEHOLDER,
    LibraryTreeModel,
)


class LibraryTreePanel(QWidget):
    root_selected = pyqtSignal(int)
    all_roots_selected = pyqtSignal()
    category_selected = pyqtSignal(str)
    add_to_database = pyqtSignal(object, int)
    open_in_explorer = pyqtSignal(object)
    delete_library_root = pyqtSignal(int)
    device_type_changed = pyqtSignal()
    discover_on_root = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    def __init__(self, db: Database, parent=None) -> None:
        super().__init__(parent)
        self.db = db
        self._filter_root_id: int | None = None
        self._last_root_count = -1
        self.setObjectName("dgLeftPanel")
        self.setMinimumWidth(260)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 4, 6)
        layout.setSpacing(4)

        title = QLabel("Devices and drives")
        title.setObjectName("dgPanelTitle")
        layout.addWidget(title)
        hint = QLabel(
            "Green = reorganized (has marker JSON)  ·  "
            "✓ = in catalog  ·  Right-click for actions"
        )
        hint.setObjectName("dgPanelHint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self._summary = QLabel("")
        self._summary.setObjectName("dgPanelHint")
        layout.addWidget(self._summary)

        self.tree = QTreeView()
        self.tree.setObjectName("dgDeviceTree")
        self.nav_model = LibraryTreeModel(self)
        self.tree.setModel(self.nav_model)
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._context_menu)
        self.tree.clicked.connect(self._on_index)
        self.tree.doubleClicked.connect(self._on_double_click)
        self.tree.setAnimated(True)
        self.tree.setIndentation(20)
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setMinimumWidth(220)
        self.tree.setMinimumHeight(160)
        self.tree.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.tree.expanded.connect(self._on_expanded)
        layout.addWidget(self.tree, 1)
        self.apply_theme(THEME_DARK)

    def apply_theme(self, theme: str) -> None:
        t = normalize_theme(theme)
        self.tree.setStyleSheet("")
        pal = self.tree.palette()
        if t == THEME_LIGHT:
            pal.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
            pal.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
            pal.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
            pal.setColor(QPalette.ColorRole.Highlight, QColor(49, 106, 197))
            pal.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        else:
            pal.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
            pal.setColor(QPalette.ColorRole.Text, QColor(224, 224, 224))
            pal.setColor(QPalette.ColorRole.AlternateBase, QColor(37, 37, 38))
            pal.setColor(QPalette.ColorRole.Highlight, QColor(9, 71, 113))
            pal.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        self.tree.setPalette(pal)
        self.tree.setAutoFillBackground(True)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self._expand_default)

    def refresh(self, filter_root_id: int | None = None, *, rebuild: bool = False) -> None:
        if filter_root_id is None:
            self._filter_root_id = None
        else:
            self._filter_root_id = filter_root_id
        roots = self.db.get_roots()
        catalog: dict[int, set[str]] = {}
        for root in roots:
            catalog[int(root["id"])] = self.db.get_extraction_paths_for_root(int(root["id"]))
        if rebuild or len(roots) != self._last_root_count:
            self._last_root_count = len(roots)
            self.nav_model.reload(roots, catalog_paths=catalog)
            self._update_summary(len(roots))
            QTimer.singleShot(0, self._expand_default)
        else:
            self.nav_model.update_catalog_paths(catalog)

        if filter_root_id is not None:
            item = self.nav_model.item_for_root_id(filter_root_id)
            if item is not None:
                idx = item.index()
                self.tree.setCurrentIndex(idx)
                self.tree.scrollTo(idx)
        elif self.nav_model.rowCount() > 0:
            idx = self.nav_model.index(0, 0)
            self.tree.setCurrentIndex(idx)

    def _update_summary(self, root_count: int) -> None:
        if root_count == 0:
            self._summary.setText("No library roots — File → Add library root…")
        else:
            self._summary.setText(
                f"{root_count} library root(s) — expand [HDD]/[SSD]… to browse folders"
            )

    def _expand_default(self) -> None:
        if self.nav_model.rowCount() == 0:
            return
        root_item = self.nav_model.invisibleRootItem()
        for r in range(root_item.rowCount()):
            item = root_item.child(r)
            if item is None:
                continue
            if self.nav_model.kind(item) == KIND_ALL:
                continue
            self.tree.expand(item.index())
            for cr in range(item.rowCount()):
                child = item.child(cr)
                if child is not None and self.nav_model.kind(child) != KIND_PLACEHOLDER:
                    self.tree.expand(child.index())

    def _item_from_index(self, index: QModelIndex):
        if not index.isValid():
            return None
        return self.nav_model.itemFromIndex(index)

    def _on_expanded(self, index: QModelIndex) -> None:
        item = self._item_from_index(index)
        if item is not None:
            self.nav_model.load_folder_children(item)

    def _on_double_click(self, index: QModelIndex) -> None:
        item = self._item_from_index(index)
        if item is not None:
            self.nav_model.load_folder_children(item)
            self.tree.expand(index)
        self._on_index(index)

    def _on_index(self, index: QModelIndex) -> None:
        item = self._item_from_index(index)
        if item is None:
            return
        kind = self.nav_model.kind(item)
        if kind in (KIND_EMPTY, KIND_PLACEHOLDER, None):
            return
        if kind == KIND_ALL:
            self._filter_root_id = None
            self.all_roots_selected.emit()
        elif kind == KIND_CATEGORY:
            dtype = self.nav_model.device_type_for_item(item)
            if dtype:
                self.category_selected.emit(dtype)
            self._filter_root_id = None
            self.all_roots_selected.emit()
        elif kind == KIND_LIBRARY_ROOT:
            root_id = self.nav_model.root_id_for_item(item)
            if root_id is not None:
                self._filter_root_id = root_id
                self.root_selected.emit(root_id)
        elif kind == KIND_FOLDER:
            root_id = self.nav_model.root_id_for_item(item)
            if root_id is not None:
                self._filter_root_id = root_id
                self.root_selected.emit(root_id)

    def _context_menu(self, pos) -> None:
        index = self.tree.indexAt(pos)
        item = self._item_from_index(index)
        if item is None:
            menu = QMenu(self)
            self._add_refresh_actions(menu)
            menu.exec(self.tree.viewport().mapToGlobal(pos))
            return
        kind = self.nav_model.kind(item)
        menu = QMenu(self)
        if kind == KIND_LIBRARY_ROOT:
            self._menu_library_root(menu, item)
        elif kind == KIND_FOLDER:
            self._menu_folder(menu, item)
        elif kind == KIND_CATEGORY:
            self._menu_category(menu, item)
        else:
            self._add_refresh_actions(menu)
        if not menu.isEmpty():
            menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _add_refresh_actions(self, menu: QMenu) -> None:
        act = QAction("Refresh tree", menu)
        act.setShortcut(QKeySequence("F5"))
        act.triggered.connect(self.refresh_requested.emit)
        menu.addAction(act)

    def _menu_library_root(self, menu: QMenu, item) -> None:
        folder = self.nav_model.path_for_item(item)
        root_id = self.nav_model.root_id_for_item(item)
        device_id = self.nav_model.device_id_for_item(item)
        if not folder or root_id is None:
            return

        open_act = QAction("Open in Explorer", menu)
        open_act.triggered.connect(lambda: self.open_in_explorer.emit(folder))
        menu.addAction(open_act)
        menu.addSeparator()

        disc_act = QAction("Discover folders on this root…", menu)
        disc_act.triggered.connect(lambda: self.discover_on_root.emit(root_id))
        menu.addAction(disc_act)

        refresh_act = QAction("Refresh status", menu)
        refresh_act.triggered.connect(self.refresh_requested.emit)
        menu.addAction(refresh_act)
        menu.addSeparator()

        type_menu = menu.addMenu("Set storage type")
        if device_id is not None:
            for dtype in DEVICE_TYPE_ORDER:
                label = DEVICE_TYPE_LABELS[dtype]
                act = QAction(label, type_menu)
                act.triggered.connect(
                    lambda _c=False, d=dtype, did=device_id: self._set_device_type(did, d)
                )
                type_menu.addAction(act)

        menu.addSeparator()
        del_act = QAction("Remove library root from catalog…", menu)
        del_act.triggered.connect(lambda: self.delete_library_root.emit(root_id))
        menu.addAction(del_act)
        menu.addSeparator()
        self._add_refresh_actions(menu)

    def _menu_folder(self, menu: QMenu, item) -> None:
        folder = self.nav_model.path_for_item(item)
        root_id = self.nav_model.root_id_for_item(item)
        if not folder or root_id is None or not folder.is_dir():
            return

        add_act = QAction("Add to database…", menu)
        add_act.setShortcut(QKeySequence("Ins"))
        add_act.triggered.connect(lambda: self.add_to_database.emit(folder, root_id))
        menu.addAction(add_act)

        open_act = QAction("Open in Explorer", menu)
        open_act.triggered.connect(lambda: self.open_in_explorer.emit(folder))
        menu.addAction(open_act)
        menu.addSeparator()
        self._add_refresh_actions(menu)

        if not check_path_accessible(folder):
            add_act.setEnabled(False)

    def _menu_category(self, menu: QMenu, item) -> None:
        expand = QAction("Expand all under this type", menu)
        expand.triggered.connect(lambda: self._expand_item(item))
        menu.addAction(expand)
        menu.addSeparator()
        self._add_refresh_actions(menu)

    def _expand_item(self, item) -> None:
        self.tree.expand(item.index())
        for r in range(item.rowCount()):
            child = item.child(r)
            if child is None:
                continue
            if self.nav_model.kind(child) == KIND_PLACEHOLDER:
                self.nav_model.load_folder_children(item)
                child = item.child(r)
            if child is not None:
                self.tree.expand(child.index())
                self.nav_model.load_folder_children(child)

    def _set_device_type(self, device_id: int, device_type: str) -> None:
        self.db.update_device_type(device_id, device_type)
        self.device_type_changed.emit()
        self.refresh(self._filter_root_id, rebuild=True)

    def select_all_roots(self) -> None:
        self._filter_root_id = None
        if self.nav_model.rowCount() > 0:
            idx = self.nav_model.index(0, 0)
            self.tree.setCurrentIndex(idx)
            self.tree.expand(idx)
