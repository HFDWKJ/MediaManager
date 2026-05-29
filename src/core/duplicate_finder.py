"""Tier 2: user-triggered hash verification."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from core.database import Database
from core.scanner import build_file_sequence, calculate_hash, detect_file_type

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int, str], None]


@dataclass
class HashVerifyResult:
    status: str  # confirmed, mismatch, partial
    message: str
    group_id: int | None = None


def verify_extraction_folders(
    db: Database,
    extraction_ids: list[int],
    chunk_size: int = 65536,
    progress: ProgressCallback | None = None,
) -> HashVerifyResult:
    if len(extraction_ids) < 2:
        return HashVerifyResult("mismatch", "Need at least 2 folders to compare")

    skip_names = {".DS_Store", "Thumbs.db", "desktop.ini"}
    skip_ext = {".crdownload", ".part", ".tmp"}

    folder_hashes: list[list[tuple[str, str, int]]] = []

    for idx, eid in enumerate(extraction_ids):
        row = db.get_extraction(eid)
        if not row:
            return HashVerifyResult("mismatch", f"Extraction {eid} not found")
        folder = Path(row["root_path"]) / row["folder_path"]
        if not folder.exists():
            return HashVerifyResult("partial", f"Folder offline or missing: {folder}")

        files = build_file_sequence(folder, skip_names, skip_ext)
        entries: list[tuple[str, str, int]] = []
        for i, fpath in enumerate(files):
            h = calculate_hash(fpath, chunk_size)
            if not h:
                return HashVerifyResult("partial", f"Could not hash {fpath}")
            entries.append((fpath.name, h, fpath.stat().st_size))
            db.upsert_media(
                root_id=int(row["root_id"]),
                relative_path=str(fpath.relative_to(Path(row["root_path"]))).replace("\\", "/"),
                absolute_path=str(fpath),
                original_name=fpath.name,
                file_size=fpath.stat().st_size,
                file_type=detect_file_type(fpath),
                extraction_id=eid,
                file_hash=h,
            )
            if progress:
                progress(i + 1, len(files), fpath.name)

        entries.sort(key=lambda x: (x[0], x[1]))
        folder_hashes.append(entries)

    if len({len(h) for h in folder_hashes}) != 1:
        return HashVerifyResult("mismatch", "Different file counts in folders")

    ref = folder_hashes[0]
    for other in folder_hashes[1:]:
        if ref != other:
            return HashVerifyResult("mismatch", "File hashes do not match across folders")

    # All identical — create duplicate group from first file hash set
    media_ids = []
    for row in db.get_media_in_extraction(extraction_ids[0]):
        if row["file_hash"]:
            matches = db.get_media_by_hash(row["file_hash"])
            for m in matches:
                media_ids.append(int(m["id"]))

    media_ids = list(dict.fromkeys(media_ids))
    if media_ids and ref:
        gid = db.create_duplicate_group(ref[0][1], ref[0][2], media_ids)
        return HashVerifyResult("confirmed", "Folders are byte-identical", gid)

    return HashVerifyResult("confirmed", "Folders match (no media rows linked)")
