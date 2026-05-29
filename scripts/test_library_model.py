"""Headless check for library nav model (run from repo root)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PyQt6.QtWidgets import QApplication
from gui.library_nav_model import LibraryNavModel, _NavNode

app = QApplication([])

rows = [
    {
        "id": 1,
        "device_type": "ssd",
        "root_path": "C:\\",
        "label": "Sample",
        "device_id": 1,
        "is_online": 1,
    }
]
m = LibraryNavModel()
m.reload(rows)
top_count = m.rowCount()
print("top rows:", top_count)
for r in range(top_count):
    idx = m.index(r, 0)
    ptr = idx.internalPointer()
    text = m.data(idx)
    kind = m.data(idx, m.NodeKindRole)
    print(f"  [{r}] text={text!r} kind={kind} ptr={type(ptr).__name__}")

cat_idx = None
for r in range(top_count):
    idx = m.index(r, 0)
    if m.data(idx, m.NodeKindRole) == _NavNode.KIND_CATEGORY:
        cat_idx = idx
        break
if cat_idx and cat_idx.isValid():
    print("category children:", m.rowCount(cat_idx))
    c0 = m.index(0, 0, cat_idx)
    print("  root0:", m.data(c0))

# Simulate set_catalog_paths after reload
m.set_catalog_paths({1: set()})
for r in range(top_count):
    idx = m.index(r, 0)
    print(f"after layoutChanged [{r}]:", m.data(idx))

print("OK")
