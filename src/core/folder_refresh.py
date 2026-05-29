"""Refresh folder status from disk without full re-import."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from core.database import Database
from core.device_manager import check_path_accessible, refresh_all_device_status
from core.scanner import summarize_folder

logger = logging.getLogger(__name__)


@dataclass
class RefreshResult:
    updated: int = 0
    offline: int = 0
    missing: int = 0


def refresh_folder_status(db: Database, config: dict, root_id: int | None = None) -> RefreshResult:
    """Update availability, file counts, and sizes for cataloged folders."""
    refresh_all_device_status(db)
    result = RefreshResult()

    skip_ext = set(e.lower() for e in config.get("scan", {}).get("skip_extensions", []))
    skip_names = set(config.get("reorganize", {}).get("skip_files", []))

    rows = db.get_extractions(root_id=root_id)
    for ext in rows:
        folder = Path(ext.root_path) / ext.folder_path.replace("\\", "/")
        if not check_path_accessible(folder):
            if ext.availability == "online":
                result.offline += 1
            db.update_extraction_fields(
                ext.id,
                availability="offline" if Path(ext.root_path).exists() else "missing",
            )
            continue

        if not folder.is_dir():
            db.update_extraction_fields(ext.id, availability="missing")
            result.missing += 1
            continue

        count, total = summarize_folder(folder, skip_names, skip_ext)
        db.update_extraction_fields(
            ext.id,
            file_count=count,
            total_size=total,
            availability="online",
        )
        db.update_root_scan(ext.root_id, count)
        result.updated += 1

    logger.info("Refresh: updated=%s offline=%s missing=%s", result.updated, result.offline, result.missing)
    return result
