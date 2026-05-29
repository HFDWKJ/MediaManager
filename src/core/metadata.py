"""Original file details for reorganize (database + CSV report)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


def capture_original_details(
    *,
    original_relative_path: str,
    original_filename: str,
    original_absolute_path: str,
    sequence_no: int,
    original_folder_name: str,
    original_folder_path: str,
    sequence_rule: str,
    new_filename: str | None = None,
    new_absolute_path: str | None = None,
    new_relative_path: str | None = None,
    file_hash: str | None = None,
    media_id: int | None = None,
) -> dict[str, Any]:
    return {
        "sequence_no": sequence_no,
        "original_relative_path": original_relative_path,
        "original_filename": original_filename,
        "original_absolute_path": original_absolute_path,
        "new_filename": new_filename,
        "new_absolute_path": new_absolute_path,
        "new_relative_path": new_relative_path,
        "original_folder_name": original_folder_name,
        "original_folder_path": original_folder_path,
        "sequence_rule": sequence_rule,
        "file_hash": file_hash,
        "media_id": media_id,
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }


def details_to_json(details: dict[str, Any]) -> str:
    return json.dumps(details, ensure_ascii=False)
