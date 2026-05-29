"""On-disk marker written after a successful reorganize."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MARKER_FILENAME = "media_manager_reorganize.json"


def marker_file_path(folder: Path) -> Path:
    return folder.resolve() / MARKER_FILENAME


def has_reorganize_marker(folder: Path) -> bool:
    folder = folder.resolve()
    if marker_file_path(folder).is_file():
        return True
    from core.reorganize_report import CSV_PREFIX

    return any(folder.glob(f"{CSV_PREFIX}*.csv"))


def read_reorganize_marker(folder: Path) -> dict[str, Any] | None:
    path = marker_file_path(folder)
    if not path.is_file():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def write_reorganize_marker(
    folder: Path,
    *,
    original_folder_name: str,
    new_folder_name: str,
    extraction_id: int | None = None,
) -> Path:
    """Write marker JSON into the reorganized folder. Returns the file path."""
    folder = folder.resolve()
    payload: dict[str, Any] = {
        "original_folder_name": original_folder_name,
        "new_folder_name": new_folder_name,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if extraction_id is not None:
        payload["extraction_id"] = extraction_id
    path = marker_file_path(folder)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return path
