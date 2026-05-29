"""Tree view model for library roots, extraction folders, and subfolders."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PyQt6.QtCore import QAbstractItemModel, QModelIndex, Qt
from PyQt6.QtGui import QColor

from core.database import Database, ExtractionRow, FOLDER_TYPE_LABELS
from core.names import format_display_name


@dataclass
class TreeNode:
    label: str
    children: list[TreeNode] = field(default_factory=list)
    parent: TreeNode | None = None
    extraction: ExtractionRow | None = None
    node_kind: str = "segment"  # root, library, segment, extraction, subfolder

    def add_child(self, child: TreeNode) -> TreeNode:
        child.parent = self
        self.children.append(child)
        return child

    def find_child(self, label: str) -> TreeNode | None:
        for c in self.children:
            if c.label == label:
                return c
        return None


class ExtractionTreeModel(QAbstractItemModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._root = TreeNode("", node_kind="root")
        self._extraction_index: dict[int, TreeNode] = {}
        self.selected_extraction_id: int | None = None

    def build(self, rows: list[ExtractionRow], db: Database) -> None:
        self.beginResetModel()
        self._root = TreeNode("All folders", node_kind="root")
        self._extraction_index.clear()

        by_root: dict[int, list[ExtractionRow]] = {}
        for row in rows:
            by_root.setdefault(row.root_id, []).append(row)

        for root_id in sorted(by_root, key=lambda rid: by_root[rid][0].root_label):
            items = sorted(by_root[root_id], key=lambda e: e.folder_path.lower())
            sample = items[0]
            lib_label = f"🟢 {sample.device_name} — {sample.root_label}"
            if sample.availability != "online":
                lib_label = f"🔴 {sample.device_name} — {sample.root_label}"
            lib_node = self._root.add_child(TreeNode(lib_label, node_kind="library"))

            for ext in items:
                self._add_extraction_path(lib_node, ext, db)

        self.endResetModel()

    def _add_extraction_path(self, lib_node: TreeNode, ext: ExtractionRow, db: Database) -> None:
        parts = self._path_parts(ext)
        current = lib_node
        for i, part in enumerate(parts):
            existing = current.find_child(part)
            if existing:
                current = existing
            else:
                current = current.add_child(TreeNode(part, node_kind="segment"))
            if i == len(parts) - 1:
                current.extraction = ext
                current.node_kind = "extraction"
                self._set_extraction_label(current, ext)
                self._extraction_index[ext.id] = current
                self._add_subfolder_nodes(current, ext, db)

    @staticmethod
    def _path_parts(ext: ExtractionRow) -> list[str]:
        if ext.folder_path in (".", ""):
            return [format_display_name(ext.original_name)]
        parts = ext.folder_path.replace("\\", "/").split("/")
        return [format_display_name(p) for p in parts if p]

    @staticmethod
    def _set_extraction_label(node: TreeNode, ext: ExtractionRow) -> None:
        name = format_display_name(ext.original_name)
        type_lbl = FOLDER_TYPE_LABELS.get(ext.folder_type, "")
        match = {
            "exact": " 🟡",
            "similar": " 🟠",
            "hash_confirmed": " 🟢",
        }.get(ext.match_status, "")
        node.label = f"📁 {name}  ({ext.file_count} files) {type_lbl}{match}"

    def _add_subfolder_nodes(
        self, parent: TreeNode, ext: ExtractionRow, db: Database, max_depth: int = 8
    ) -> None:
        sub_names = self._collect_subfolder_names(ext, db)
        extraction_dir = Path(ext.root_path) / ext.folder_path.replace("\\", "/")
        if extraction_dir.is_dir():
            try:
                for child in extraction_dir.iterdir():
                    if child.is_dir() and not child.name.startswith("."):
                        sub_names.add(child.name)
            except OSError:
                pass

        for name in sorted(sub_names, key=str.lower):
            if parent.find_child(f"📂 {name}"):
                continue
            sub_node = parent.add_child(TreeNode(f"📂 {name}", node_kind="subfolder"))
            if extraction_dir.is_dir():
                child_path = extraction_dir / name
                if child_path.is_dir() and max_depth > 1:
                    self._add_nested_subfolders(sub_node, child_path, max_depth - 1)

    def _add_nested_subfolders(self, parent: TreeNode, path: Path, depth: int) -> None:
        if depth <= 0:
            return
        try:
            for child in sorted(path.iterdir()):
                if child.is_dir() and not child.name.startswith("."):
                    label = f"📂 {child.name}"
                    if not parent.find_child(label):
                        nested = parent.add_child(TreeNode(label, node_kind="subfolder"))
                        self._add_nested_subfolders(nested, child, depth - 1)
        except OSError:
            pass

    @staticmethod
    def _collect_subfolder_names(ext: ExtractionRow, db: Database) -> set[str]:
        names: set[str] = set()
        prefix = ext.folder_path.replace("\\", "/").rstrip("/")
        if prefix in ("", "."):
            prefix = ""
        else:
            prefix = prefix + "/"

        for media in db.get_media_in_extraction(ext.id):
            fp = (media["folder_path"] or "").replace("\\", "/")
            if not fp:
                continue
            if prefix and fp.startswith(prefix):
                rest = fp[len(prefix) :]
            elif not prefix:
                rest = fp
            else:
                continue
            first = rest.split("/")[0]
            if first and first not in (".", ""):
                names.add(first)
        return names

    def node_from_index(self, index: QModelIndex) -> TreeNode | None:
        if not index.isValid():
            return None
        return index.internalPointer()

    def extraction_from_index(self, index: QModelIndex) -> ExtractionRow | None:
        node = self.node_from_index(index)
        if node and node.extraction:
            return node.extraction
        return None

    def extraction_by_id(self, extraction_id: int) -> ExtractionRow | None:
        node = self._extraction_index.get(extraction_id)
        return node.extraction if node else None

    def index_for_extraction(self, extraction_id: int) -> QModelIndex:
        node = self._extraction_index.get(extraction_id)
        if not node or not node.parent:
            return QModelIndex()
        row = node.parent.children.index(node)
        return self.createIndex(row, 0, node)

    # --- QAbstractItemModel ---
    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parent_node = parent.internalPointer() if parent.isValid() else self._root
        if row < 0 or row >= len(parent_node.children):
            return QModelIndex()
        return self.createIndex(row, column, parent_node.children[row])

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()
        child: TreeNode = index.internalPointer()
        parent_node = child.parent
        if parent_node is None or parent_node is self._root:
            return QModelIndex()
        grand = parent_node.parent
        if grand is None:
            return QModelIndex()
        row = grand.children.index(parent_node)
        return self.createIndex(row, 0, parent_node)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        parent_node = parent.internalPointer() if parent.isValid() else self._root
        return len(parent_node.children)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 1

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        node: TreeNode = index.internalPointer()

        if role == Qt.ItemDataRole.DisplayRole:
            return node.label

        if role == Qt.ItemDataRole.ToolTipRole and node.extraction:
            ext = node.extraction
            return (
                f"{ext.root_path}\\{ext.folder_path}\n"
                f"{ext.file_count} files, {ext.total_size / 1024 / 1024:.1f} MB"
            )

        if role == Qt.ItemDataRole.BackgroundRole:
            if node.extraction and node.extraction.id == self.selected_extraction_id:
                return None
            if node.extraction:
                ext = node.extraction
                if ext.folder_type == "root":
                    return QColor(35, 45, 65)
                if ext.match_status == "exact":
                    return QColor(80, 70, 20)
                if ext.match_status == "similar":
                    return QColor(80, 50, 20)
            return None

        if role == Qt.ItemDataRole.UserRole and node.extraction:
            return node.extraction.id

        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        node: TreeNode = index.internalPointer()
        base = Qt.ItemFlag.ItemIsEnabled
        if node.extraction is not None:
            return base | Qt.ItemFlag.ItemIsSelectable
        return base
