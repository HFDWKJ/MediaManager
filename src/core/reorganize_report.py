"""Single CSV report per reorganize run (timestamped filename)."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CSV_PREFIX = "reorganize_"
CSV_COLUMNS = [
    "sequence_no",
    "original_relative_path",
    "original_filename",
    "original_absolute_path",
    "new_filename",
    "new_absolute_path",
    "new_relative_path",
    "original_folder_name",
    "original_folder_path",
    "file_hash",
    "media_id",
    "processed_at",
]


def report_filename(processed_at: datetime | None = None) -> str:
    ts = processed_at or datetime.now(timezone.utc)
    local = ts.astimezone()
    return f"{CSV_PREFIX}{local.strftime('%Y%m%d_%H%M%S')}.csv"


def write_reorganize_csv(
    folder: Path,
    rows: list[dict[str, Any]],
    *,
    processed_at: datetime | None = None,
) -> Path:
    """Write all file rows for one reorganize run into a single CSV in `folder`."""
    folder = folder.resolve()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / report_filename(processed_at)
    when = (processed_at or datetime.now(timezone.utc)).isoformat()
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out.setdefault("processed_at", when)
            writer.writerow(out)
    return path


def find_latest_reorganize_csv(folder: Path) -> Path | None:
    folder = folder.resolve()
    candidates = sorted(folder.glob(f"{CSV_PREFIX}*.csv"), reverse=True)
    return candidates[0] if candidates else None
