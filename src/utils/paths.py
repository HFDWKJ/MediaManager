"""Application and portable (portal) data paths."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PORTABLE_MARKER = "portable.marker"
DATA_DIR_NAME = "data"


def application_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def is_portable_mode() -> bool:
    env = os.environ.get("MEDIA_MANAGER_PORTABLE", "").strip().casefold()
    if env in ("1", "true", "yes", "on"):
        return True
    return (application_root() / PORTABLE_MARKER).is_file()


def data_dir() -> Path:
    """Directory for config, database, and logs."""
    if is_portable_mode():
        path = application_root() / DATA_DIR_NAME
        path.mkdir(parents=True, exist_ok=True)
        return path
    return _installed_config_dir()


def _installed_config_dir() -> Path:
    path = Path(os.environ.get("APPDATA", Path.home())) / "MediaManager"
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_file_path() -> Path:
    return data_dir() / "config.json"


def catalog_db_path() -> Path:
    return data_dir() / "catalog.db"


def log_dir() -> Path:
    logs = data_dir() / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    return logs
