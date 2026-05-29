"""Export and import the Media Manager SQLite catalog."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

CATALOG_TABLES = (
    "StorageDevice",
    "LibraryRoot",
    "ExtractionFolder",
    "Media",
    "Metadata",
    "Face_UID",
)


class CatalogTransferError(ValueError):
    """Raised when a file is not a valid Media Manager catalog."""


def default_export_filename() -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"media_manager_catalog_{stamp}.db"


def validate_catalog_database(path: Path) -> None:
    if not path.is_file():
        raise CatalogTransferError(f"File not found: {path}")
    try:
        conn = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    except sqlite3.Error as e:
        raise CatalogTransferError(f"Cannot open database: {e}") from e
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        tables = {str(r[0]) for r in rows}
        missing = [name for name in CATALOG_TABLES if name not in tables]
        if missing:
            raise CatalogTransferError(
                "The selected file is not a valid Media Manager catalog "
                f"(missing tables: {', '.join(missing)})."
            )
    finally:
        conn.close()


def _remove_sqlite_sidecars(db_path: Path) -> None:
    for suffix in ("-wal", "-shm"):
        sidecar = Path(f"{db_path}{suffix}")
        if sidecar.exists():
            sidecar.unlink()


def copy_catalog_database(source: Path, dest: Path) -> None:
    """Copy catalog contents from source to dest using SQLite's online backup API."""
    source = source.resolve()
    dest = dest.resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists() and dest != source:
        _remove_sqlite_sidecars(dest)

    src_conn = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    if dest.exists() and dest == source:
        raise CatalogTransferError("Source and destination must be different files.")
    dest_conn = sqlite3.connect(dest)
    try:
        src_conn.backup(dest_conn)
    finally:
        src_conn.close()
        dest_conn.close()


def export_catalog_database(catalog_path: Path, export_path: Path) -> None:
    validate_catalog_database(catalog_path)
    if export_path.resolve() == catalog_path.resolve():
        raise CatalogTransferError("Cannot export the catalog to itself.")
    copy_catalog_database(catalog_path, export_path)


def import_catalog_database(import_path: Path, catalog_path: Path) -> None:
    validate_catalog_database(import_path)
    if import_path.resolve() == catalog_path.resolve():
        raise CatalogTransferError("Cannot import the catalog from itself.")
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    _remove_sqlite_sidecars(catalog_path)
    copy_catalog_database(import_path, catalog_path)
