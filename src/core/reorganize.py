"""Flatten and rename new extraction folders."""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from core.database import Database, FOLDER_TYPE_COLLECTION
from core.metadata import capture_original_details, details_to_json
from core.name_matcher import folder_name_on_disk, normalize_name, safe_new_folder_name
from core.names import strip_bracket_wrapper
from core.reorganize_marker import write_reorganize_marker
from core.reorganize_report import write_reorganize_csv
from core.scanner import (
    build_file_sequence,
    calculate_hash,
    detect_file_type,
    file_mtime_iso,
    reorganize_file_prefix,
)

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int, str], None]


@dataclass
class ReorganizeRow:
    sequence: int
    original_relative: str
    original_filename: str
    new_filename: str
    original_absolute: str


@dataclass
class ReorganizePlan:
    extraction_id: int
    new_folder_name: str
    target_folder_name: str
    source_folder: Path
    root_path: Path
    rows: list[ReorganizeRow]


def build_reorganize_plan(
    db: Database,
    extraction_id: int,
    new_folder_name: str,
    config: dict,
) -> ReorganizePlan | None:
    row = db.get_extraction(extraction_id)
    if not row:
        return None

    folder_type = row["folder_type"] or FOLDER_TYPE_COLLECTION
    if folder_type != FOLDER_TYPE_COLLECTION:
        logger.warning("Reorganize blocked: extraction %s is type %s", extraction_id, folder_type)
        return None

    root_path = Path(row["root_path"])
    source = root_path / row["folder_path"]
    if not source.is_dir():
        return None

    safe = safe_new_folder_name(strip_bracket_wrapper(new_folder_name))
    target_name = folder_name_on_disk(safe)
    template = config.get("reorganize", {}).get(
        "filename_template", "{filetype}_{new_folder_name}_{seq:04d}_{hash8}{ext}"
    )
    skip_names = set(config.get("reorganize", {}).get("skip_files", []))
    skip_ext = set(config.get("scan", {}).get("skip_extensions", []))
    prefix_overrides = config.get("reorganize", {}).get("filetype_prefixes")

    files = build_file_sequence(source, skip_names, skip_ext)
    rows: list[ReorganizeRow] = []
    safe_token = safe.replace(" ", "_")

    for seq, fpath in enumerate(files, 1):
        rel = str(fpath.relative_to(source)).replace("\\", "/")
        file_hash = calculate_hash(fpath) or "00000000"
        hash8 = file_hash[:8]
        ftype = reorganize_file_prefix(fpath, prefix_overrides)
        new_name = template.format(
            filetype=ftype,
            new_folder_name=safe_token,
            seq=seq,
            hash8=hash8,
            ext=fpath.suffix.lower(),
        )
        rows.append(
            ReorganizeRow(
                sequence=seq,
                original_relative=rel,
                original_filename=fpath.name,
                new_filename=new_name,
                original_absolute=str(fpath.resolve()),
            )
        )

    return ReorganizePlan(
        extraction_id=extraction_id,
        new_folder_name=safe,
        target_folder_name=target_name,
        source_folder=source,
        root_path=root_path,
        rows=rows,
    )


def _join_rel(*parts: str) -> str:
    cleaned = [p.replace("\\", "/").strip("/") for p in parts if p and p.strip("/")]
    return "/".join(cleaned)


def _sync_extraction_media(
    db: Database,
    plan: ReorganizePlan,
    root_id: int,
    new_folder_rel: str,
    media_updates: dict[str, int],
) -> None:
    """Ensure Media rows match flat files on disk after reorganize."""
    folder = plan.source_folder
    kept_ids: set[int] = set()

    for row in plan.rows:
        dst = folder / row.new_filename
        if not dst.is_file():
            continue
        new_relative = _join_rel(new_folder_rel, row.new_filename)
        new_abs = str(dst.resolve())
        file_hash = calculate_hash(dst) or None
        file_size = dst.stat().st_size
        parent = new_folder_rel if new_folder_rel != "." else ""

        media_id = media_updates.get(row.new_filename)
        if media_id is None:
            existing = db.find_media_by_relative(root_id, new_relative)
            if existing is not None:
                media_id = int(existing["id"])

        if media_id is not None:
            db.update_media_for_reorganize(
                media_id,
                relative_path=new_relative,
                absolute_path=new_abs,
                original_name=row.new_filename,
                file_size=file_size,
                file_type=detect_file_type(dst),
                folder_path=parent,
                depth=max(0, len(Path(new_relative).parts) - 1),
                file_hash=file_hash,
                mtime=file_mtime_iso(dst),
            )
            kept_ids.add(media_id)
        else:
            new_id = db.upsert_media(
                root_id=root_id,
                relative_path=new_relative,
                absolute_path=new_abs,
                original_name=row.new_filename,
                file_size=file_size,
                file_type=detect_file_type(dst),
                extraction_id=plan.extraction_id,
                folder_path=parent,
                depth=max(0, len(Path(new_relative).parts) - 1),
                file_hash=file_hash,
                mtime=file_mtime_iso(dst),
            )
            kept_ids.add(new_id)

    orphan_ids = [
        int(m["id"])
        for m in db.get_media_in_extraction(plan.extraction_id)
        if int(m["id"]) not in kept_ids
    ]
    if orphan_ids:
        db.delete_media_ids(orphan_ids)
        logger.info("Removed %s stale Media row(s) after sync", len(orphan_ids))


def execute_reorganize(
    db: Database,
    plan: ReorganizePlan,
    config: dict,
    progress: ProgressCallback | None = None,
) -> bool:
    ext_before = db.get_extraction(plan.extraction_id)
    if not ext_before:
        return False

    root_id = int(ext_before["root_id"])
    old_folder_path = str(ext_before["folder_path"]).replace("\\", "/")
    pre_path = ext_before["pre_reorganize_folder_path"] or old_folder_path
    pre_name = ext_before["pre_reorganize_folder_name"] or str(
        ext_before["original_name"] or plan.source_folder.name
    )

    processed_at = datetime.now(timezone.utc)

    target_dir = plan.root_path / plan.target_folder_name
    if target_dir.exists() and target_dir != plan.source_folder:
        logger.error("Target folder already exists: %s", target_dir)
        return False

    if plan.source_folder.name != plan.target_folder_name:
        new_source = plan.source_folder.parent / plan.target_folder_name
        if not plan.source_folder.exists():
            return False
        if new_source.exists():
            plan.source_folder = new_source
        else:
            plan.source_folder.rename(new_source)
            plan.source_folder = new_source

    sequence_rule = config.get("reorganize", {}).get(
        "sequence_rule", "root_files_first_then_subfolders_by_path"
    )
    new_folder_rel = str(plan.source_folder.relative_to(plan.root_path)).replace("\\", "/")

    csv_rows: list[dict] = []
    media_updates: dict[str, int] = {}
    total = len(plan.rows)

    for i, row in enumerate(plan.rows, 1):
        src = plan.source_folder / row.original_relative
        if not src.exists():
            src = Path(row.original_absolute)
        dst = plan.source_folder / row.new_filename

        old_relative = _join_rel(old_folder_path, row.original_relative)
        new_relative = _join_rel(new_folder_rel, row.new_filename)

        file_hash_before = calculate_hash(src) if src.is_file() else None

        media_row = db.find_media_for_reorganize(
            plan.extraction_id,
            root_id,
            old_relative,
            row.original_absolute,
            file_hash=file_hash_before,
        )
        media_id: int | None = int(media_row["id"]) if media_row is not None else None

        if src.resolve() != dst.resolve():
            shutil.move(str(src), str(dst))

        if not dst.exists():
            logger.warning("File missing after move: %s", dst)
            continue

        file_hash_after = calculate_hash(dst) or file_hash_before
        new_abs = str(dst.resolve())

        if media_id is not None:
            media_updates[row.new_filename] = media_id
            db.update_media_for_reorganize(
                media_id,
                relative_path=new_relative,
                absolute_path=new_abs,
                original_name=row.new_filename,
                file_size=dst.stat().st_size,
                file_type=detect_file_type(dst),
                folder_path=new_folder_rel if new_folder_rel != "." else "",
                depth=max(0, len(Path(new_relative).parts) - 1),
                file_hash=file_hash_after,
                mtime=file_mtime_iso(dst),
            )
            details = capture_original_details(
                original_relative_path=row.original_relative,
                original_filename=row.original_filename,
                original_absolute_path=row.original_absolute,
                sequence_no=row.sequence,
                original_folder_name=pre_name,
                original_folder_path=pre_path,
                sequence_rule=sequence_rule,
                new_filename=row.new_filename,
                new_absolute_path=new_abs,
                new_relative_path=new_relative,
                file_hash=file_hash_after,
                media_id=media_id,
            )
            db.upsert_metadata(
                media_id,
                original_filename=row.original_filename,
                original_details=details_to_json(details),
            )
        else:
            details = capture_original_details(
                original_relative_path=row.original_relative,
                original_filename=row.original_filename,
                original_absolute_path=row.original_absolute,
                sequence_no=row.sequence,
                original_folder_name=pre_name,
                original_folder_path=pre_path,
                sequence_rule=sequence_rule,
                new_filename=row.new_filename,
                new_absolute_path=new_abs,
                new_relative_path=new_relative,
                file_hash=file_hash_after,
                media_id=None,
            )

        csv_rows.append(details)

        if progress:
            progress(i, total, row.new_filename)

    _sync_extraction_media(db, plan, root_id, new_folder_rel, media_updates)

    if config.get("reorganize", {}).get("write_csv", True):
        csv_path = write_reorganize_csv(
            plan.source_folder, csv_rows, processed_at=processed_at
        )
        logger.info("Wrote reorganize report: %s", csv_path)
    else:
        csv_path = None

    if config.get("reorganize", {}).get("delete_empty_subfolders", True):
        for p in sorted(plan.source_folder.rglob("*"), reverse=True):
            if p.is_dir() and not any(p.iterdir()):
                try:
                    p.rmdir()
                except OSError:
                    pass

    total_size = sum(
        (plan.source_folder / r.new_filename).stat().st_size
        for r in plan.rows
        if (plan.source_folder / r.new_filename).exists()
    )

    display_name = plan.new_folder_name
    catalog_updates: dict = {
        "folder_path": new_folder_rel,
        "original_name": display_name,
        "normalized_name": normalize_name(display_name),
        "new_folder_name": plan.new_folder_name,
        "reorganize_status": "completed",
        "file_count": len(plan.rows),
        "total_size": total_size,
    }
    if not ext_before["pre_reorganize_folder_path"]:
        catalog_updates["pre_reorganize_folder_path"] = old_folder_path
        catalog_updates["pre_reorganize_folder_name"] = pre_name
    db.update_extraction_catalog(plan.extraction_id, **catalog_updates)
    db.set_new_folder_name(plan.extraction_id, plan.new_folder_name)
    db.set_reorganize_status(plan.extraction_id, "completed")
    db.log_event(
        "reorganized",
        old_path=old_folder_path,
        extraction_id=plan.extraction_id,
        details=str(csv_path.name) if csv_path else plan.target_folder_name,
    )
    try:
        marker_payload = write_reorganize_marker(
            plan.source_folder,
            original_folder_name=pre_name,
            new_folder_name=plan.new_folder_name,
            extraction_id=plan.extraction_id,
        )
        if csv_path is not None:
            data = {}
            try:
                with open(marker_payload, encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError):
                data = {}
            data["report_csv"] = csv_path.name
            with open(marker_payload, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError as e:
        logger.warning("Could not write reorganize marker in %s: %s", plan.source_folder, e)
    return True
