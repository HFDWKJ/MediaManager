"""Library tree backed by QStandardItemModel (reliable rendering on Windows)."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QStandardItem, QStandardItemModel

from core.reorganize_marker import has_reorganize_marker

from core.device_types import (
    DEVICE_TYPE_ICONS,
    DEVICE_TYPE_LABELS,
    DEVICE_TYPE_ORDER,
    DEVICE_TYPE_UNKNOWN,
    normalize_device_type,
)

ROLE_KIND = Qt.ItemDataRole.UserRole + 1
ROLE_PATH = Qt.ItemDataRole.UserRole + 2
ROLE_ROOT_ID = Qt.ItemDataRole.UserRole + 3
ROLE_DEVICE_ID = Qt.ItemDataRole.UserRole + 4
ROLE_DEVICE_TYPE = Qt.ItemDataRole.UserRole + 5
ROLE_FETCHED = Qt.ItemDataRole.UserRole + 6

KIND_ALL = "all"
KIND_CATEGORY = "category"
KIND_LIBRARY_ROOT = "library_root"
KIND_FOLDER = "folder"
KIND_EMPTY = "empty"
KIND_PLACEHOLDER = "placeholder"

COLOR_REORGANIZED = QColor("#3fb950")


class LibraryTreeModel(QStandardItemModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setColumnCount(1)
        self._catalog_paths: dict[int, set[str]] = {}
        self._roots_data: list = []

    def reload(
        self,
        roots_rows: list,
        *,
        catalog_paths: dict[int, set[str]] | None = None,
    ) -> None:
        if catalog_paths is not None:
            self._catalog_paths = catalog_paths
        self._roots_data = list(roots_rows)
        self.clear()
        self.setHorizontalHeaderLabels(["Library"])

        if not roots_rows:
            empty = self._item("No library roots — File → Add library root…", KIND_EMPTY)
            self.invisibleRootItem().appendRow(empty)
            return

        # Filter shortcut only — each drive appears once under its device type below.
        all_item = self._item(
            f"All library roots ({len(roots_rows)}) — click to show all in catalog",
            KIND_ALL,
        )
        self.invisibleRootItem().appendRow(all_item)

        by_type: dict[str, list] = {t: [] for t in DEVICE_TYPE_ORDER}
        for row in roots_rows:
            try:
                dtype = normalize_device_type(row["device_type"])
            except (KeyError, IndexError, TypeError):
                dtype = DEVICE_TYPE_UNKNOWN
            by_type[dtype].append(row)

        for dtype in DEVICE_TYPE_ORDER:
            items = by_type.get(dtype, [])
            if not items:
                continue
            tag = DEVICE_TYPE_ICONS.get(dtype, "")
            title = DEVICE_TYPE_LABELS.get(dtype, dtype.upper())
            cat = self._item(f"{tag} {title} ({len(items)})", KIND_CATEGORY, device_type=dtype)
            self.invisibleRootItem().appendRow(cat)
            for row in sorted(items, key=lambda r: (r["label"] or r["root_path"]).lower()):
                cat.appendRow(self._library_root_item(row))

    def update_catalog_paths(self, by_root: dict[int, set[str]]) -> None:
        self._catalog_paths = by_root
        self._refresh_decorations(self.invisibleRootItem())

    def _refresh_decorations(self, parent: QStandardItem) -> None:
        for r in range(parent.rowCount()):
            child = parent.child(r)
            if child is None or self.kind(child) == KIND_PLACEHOLDER:
                continue
            if self.kind(child) == KIND_FOLDER:
                self._apply_folder_appearance(child)
            self._refresh_decorations(child)

    def _item(
        self,
        label: str,
        kind: str,
        *,
        path: Path | None = None,
        root_id: int | None = None,
        device_id: int | None = None,
        device_type: str | None = None,
    ) -> QStandardItem:
        item = QStandardItem(label)
        item.setEditable(False)
        item.setData(kind, ROLE_KIND)
        if path is not None:
            item.setData(str(path), ROLE_PATH)
        if root_id is not None:
            item.setData(root_id, ROLE_ROOT_ID)
        if device_id is not None:
            item.setData(device_id, ROLE_DEVICE_ID)
        if device_type is not None:
            item.setData(device_type, ROLE_DEVICE_TYPE)
        item.setData(False, ROLE_FETCHED)
        if kind in (KIND_LIBRARY_ROOT, KIND_FOLDER) and path and path.is_dir():
            if self._dir_has_subdirs(path):
                item.appendRow(self._placeholder_child())
        return item

    @staticmethod
    def _placeholder_child() -> QStandardItem:
        ph = QStandardItem("…")
        ph.setEditable(False)
        ph.setEnabled(False)
        ph.setData(KIND_PLACEHOLDER, ROLE_KIND)
        return ph

    @staticmethod
    def _dir_has_subdirs(path: Path) -> bool:
        try:
            return any(
                p.is_dir() and not p.name.startswith(".")
                for p in path.iterdir()
            )
        except OSError:
            return False

    def _library_root_item(self, row) -> QStandardItem:
        rid = int(row["id"])
        dtype = normalize_device_type(row["device_type"])
        online = bool(row["is_online"]) if row["is_online"] is not None else True
        status = "on" if online else "off"
        root_path = Path(row["root_path"])
        label = row["label"] or root_path.name
        drive = root_path.drive or str(root_path.anchor) or "path"
        dtype_lbl = DEVICE_TYPE_LABELS.get(dtype, dtype.upper())
        text = f"[{status}] {dtype_lbl} {drive}  {label}"
        return self._item(
            text,
            KIND_LIBRARY_ROOT,
            path=root_path,
            root_id=rid,
            device_id=int(row["device_id"]),
            device_type=dtype,
        )

    def kind(self, item: QStandardItem | None) -> str | None:
        if item is None:
            return None
        v = item.data(ROLE_KIND)
        return str(v) if v else None

    def path_for_item(self, item: QStandardItem | None) -> Path | None:
        if item is None:
            return None
        raw = item.data(ROLE_PATH)
        return Path(str(raw)) if raw else None

    def root_id_for_item(self, item: QStandardItem | None) -> int | None:
        if item is None:
            return None
        v = item.data(ROLE_ROOT_ID)
        return int(v) if v is not None else None

    def device_id_for_item(self, item: QStandardItem | None) -> int | None:
        if item is None:
            return None
        v = item.data(ROLE_DEVICE_ID)
        return int(v) if v is not None else None

    def device_type_for_item(self, item: QStandardItem | None) -> str | None:
        if item is None:
            return None
        v = item.data(ROLE_DEVICE_TYPE)
        return str(v) if v else None

    def item_for_root_id(self, root_id: int) -> QStandardItem | None:
        def walk(parent: QStandardItem) -> QStandardItem | None:
            for r in range(parent.rowCount()):
                child = parent.child(r)
                if child is None:
                    continue
                if self.kind(child) == KIND_LIBRARY_ROOT and self.root_id_for_item(child) == root_id:
                    return child
                found = walk(child)
                if found is not None:
                    return found
            return None

        return walk(self.invisibleRootItem())

    def load_folder_children(self, item: QStandardItem) -> None:
        if item.data(ROLE_FETCHED):
            return
        kind = self.kind(item)
        if kind not in (KIND_LIBRARY_ROOT, KIND_FOLDER):
            return
        path = self.path_for_item(item)
        if not path or not path.is_dir():
            item.setData(True, ROLE_FETCHED)
            return

        item.setData(True, ROLE_FETCHED)
        item.removeRows(0, item.rowCount())

        root_id = self.root_id_for_item(item)
        device_id = self.device_id_for_item(item)
        device_type = self.device_type_for_item(item)
        root_path = self._library_root_path(root_id) if root_id else None

        try:
            entries = sorted(
                (p for p in path.iterdir() if p.is_dir() and not p.name.startswith(".")),
                key=lambda p: p.name.lower(),
            )
        except OSError:
            entries = []

        for p in entries:
            child = self._folder_item(
                p,
                root_id=root_id,
                root_path=root_path,
                device_id=device_id,
                device_type=device_type,
            )
            item.appendRow(child)

    def _folder_item(
        self,
        folder: Path,
        *,
        root_id: int | None,
        root_path: Path | None,
        device_id: int | None,
        device_type: str | None,
    ) -> QStandardItem:
        child = self._item(
            folder.name,
            KIND_FOLDER,
            path=folder,
            root_id=root_id,
            device_id=device_id,
            device_type=device_type,
        )
        self._apply_folder_appearance(child)
        return child

    def _apply_folder_appearance(self, item: QStandardItem) -> None:
        folder = self.path_for_item(item)
        if folder is None:
            return
        root_id = self.root_id_for_item(item)
        root_path = self._library_root_path(root_id) if root_id else None
        label = folder.name
        in_catalog = False
        if root_id is not None and root_path is not None:
            try:
                rel = str(folder.resolve().relative_to(root_path)).replace("\\", "/")
                in_catalog = rel in self._catalog_paths.get(root_id, set())
            except ValueError:
                pass
        if in_catalog:
            label = f"{label} ✓"
        item.setText(label)
        if has_reorganize_marker(folder):
            item.setForeground(QBrush(COLOR_REORGANIZED))
        else:
            item.setData(None, Qt.ItemDataRole.ForegroundRole)

    def _library_root_path(self, root_id: int) -> Path | None:
        for row in self._roots_data:
            if int(row["id"]) == root_id:
                return Path(row["root_path"]).resolve()
        return None
