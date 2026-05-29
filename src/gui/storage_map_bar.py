"""DiskGenius-style horizontal storage overview bar."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QSizePolicy, QWidget

from gui.dg_theme import THEME_DARK, normalize_theme, storage_map_colors


class StorageMapBar(QWidget):
    """Colored segments for library roots (like partition bar in DiskGenius)."""

    COLORS = [
        "#e67e22",
        "#e84393",
        "#3498db",
        "#2ecc71",
        "#9b59b6",
        "#1abc9c",
        "#f39c12",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("storageMapBar")
        self.setMinimumHeight(52)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._segments: list[dict] = []
        self._title = "Storage map"
        self._theme = THEME_DARK

    def set_theme(self, theme: str) -> None:
        self._theme = normalize_theme(theme)
        self.update()

    def set_segments(self, title: str, segments: list[dict]) -> None:
        """segments: [{label, size, selected}, ...] size in bytes for width ratio."""
        self._title = title
        self._segments = segments
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(8, 4, -8, -4)

        colors = storage_map_colors(self._theme)
        p.fillRect(self.rect(), colors["bg"])
        p.setPen(colors["title"])
        p.setFont(QFont("Segoe UI", 9))
        p.drawText(10, 14, self._title)

        bar_top = 22
        bar_rect = QRect(rect.left(), bar_top, rect.width(), rect.height() - bar_top + 4)
        p.fillRect(bar_rect, colors["bar"])
        p.setPen(QPen(colors["bar_border"]))

        if not self._segments:
            p.setPen(colors["empty"])
            p.drawText(bar_rect, Qt.AlignmentFlag.AlignCenter, "Select a device or library root on the left")
            p.end()
            return

        total = sum(max(int(s.get("size") or 0), 1) for s in self._segments)
        x = bar_rect.left() + 2
        right = bar_rect.right() - 2
        width = max(right - x, 1)

        for i, seg in enumerate(self._segments):
            share = max(int(seg.get("size") or 0), 1) / total
            w = max(int(width * share), 24)
            if x + w > right:
                w = right - x
            if w <= 0:
                break
            color = QColor(self.COLORS[i % len(self.COLORS)])
            if seg.get("selected"):
                color = color.lighter(115)
            seg_rect = QRect(x, bar_rect.top() + 2, w - 2, bar_rect.height() - 4)
            p.fillRect(seg_rect, color)
            p.setPen(colors["seg_border"])
            p.drawRect(seg_rect)
            p.setPen(colors["seg_text"])
            label = str(seg.get("label", ""))[:18]
            p.drawText(seg_rect.adjusted(4, 0, -4, 0), Qt.AlignmentFlag.AlignVCenter, label)
            x += w

        p.end()

    @staticmethod
    def stylesheet(theme: str) -> str:
        from gui.dg_theme import storage_map_stylesheet

        return storage_map_stylesheet(theme)
