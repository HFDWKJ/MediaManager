"""Media Manager — application entry point."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src is on path when run as script
_SRC = Path(__file__).resolve().parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from PyQt6.QtWidgets import QApplication

from core.database import Database
from core.device_manager import refresh_all_device_status
from gui.dg_theme import THEME_DARK, apply_theme, normalize_theme
from gui.main_window import MainWindow
from utils.config import load_config
from utils.logging import setup_logging
from version import __version__


def main() -> int:
    setup_logging()
    app_config = load_config()
    db = Database(app_config.catalog_db)
    refresh_all_device_status(db)

    app = QApplication(sys.argv)
    app.setApplicationName("Media Manager")
    app.setApplicationVersion(__version__)
    theme = normalize_theme(app_config.get("ui", "theme", default=THEME_DARK))
    apply_theme(app, theme)
    window = MainWindow(db, app_config)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
