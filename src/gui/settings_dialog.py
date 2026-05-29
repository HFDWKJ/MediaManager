"""Application settings dialog."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
)

from gui.dg_theme import THEME_DARK, THEME_LABELS, THEME_LIGHT, normalize_theme
from utils.config import AppConfig


class SettingsDialog(QDialog):
    def __init__(self, app_config: AppConfig, parent=None) -> None:
        super().__init__(parent)
        self.app_config = app_config
        self.setWindowTitle("Settings")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Appearance and UI options"))

        form = QFormLayout()
        self.theme_combo = QComboBox()
        for key in (THEME_DARK, THEME_LIGHT):
            self.theme_combo.addItem(THEME_LABELS[key], key)
        current = normalize_theme(app_config.get("ui", "theme", default=THEME_DARK))
        idx = self.theme_combo.findData(current)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        form.addRow("Theme:", self.theme_combo)
        layout.addLayout(form)

        hint = QLabel(
            "Dark (DiskGenius) uses charcoal panels and blue selection.\n"
            "Light (classic) uses the original beige Windows tool style."
        )
        hint.setWordWrap(True)
        hint.setObjectName("dgPanelHint")
        layout.addWidget(hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_theme(self) -> str:
        data = self.theme_combo.currentData()
        return normalize_theme(str(data) if data else THEME_DARK)
