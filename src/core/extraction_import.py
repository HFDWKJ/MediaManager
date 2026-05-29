"""Register extraction folders after user approval."""

from __future__ import annotations

import logging
from pathlib import Path

from core.database import Database, FOLDER_TYPE_COLLECTION
from core.folder_preview import FolderPreview, discover_folder_previews
from core.name_matcher import create_or_update_name_match_group, normalize_name
from core.names import format_display_name
from core.scanner import (
    detect_file_type,
    file_mtime_iso,
    iter_all_files,
)

logger = logging.getLogger(__name__)


def find_library_root_for_folder(db: Database, folder: Path) -> tuple[int, Path] | None:
    resolved = folder.resolve()
    best_id: int | None = None
    best_root: Path | None = None
    best_len = -1

    for root in db.get_roots():
        root_path = Path(root["root_path"]).resolve()
        try:
            resolved.relative_to(root_path)
        except ValueError:
            continue
        key_len = len(str(root_path))
        if key_len > best_len:
            best_len = key_len
            best_id = int(root["id"])
            best_root = root_path

    if best_id is None or best_root is None:
        return None
    return best_id, best_root


def preview_single_folder(
    db: Database,
    folder_path: Path | str,
    config: dict,
    root_id: int | None = None,
) -> FolderPreview:
    folder = Path(folder_path).resolve()
    if not folder.is_dir():
        raise FileNotFoundError(f"Not a folder: {folder}")

    if root_id is not None:
        root_row = next((r for r in db.get_roots() if int(r["id"]) == root_id), None)
        if not root_row:
            raise ValueError(f"Library root id {root_id} not found")
        lib_root_id = root_id
        root_path = Path(root_row["root_path"]).resolve()
        device_name = root_row["device_name"]
        root_label = root_row["label"] or root_row["root_path"]
    else:
        found = find_library_root_for_folder(db, folder)
        if not found:
            raise ValueError(
                "This folder is not inside any library root. "
                "Add a library root first, or choose a folder inside one."
            )
        lib_root_id, root_path = found
        root_row = next((r for r in db.get_roots() if int(r["id"]) == lib_root_id), None)
        device_name = root_row["device_name"] if root_row else ""
        root_label = (root_row["label"] or root_row["root_path"]) if root_row else ""

    rel_folder = str(folder.relative_to(root_path)).replace("\\", "/")
    existing = db.get_extraction_paths_for_root(lib_root_id)

    original = format_display_name(folder.name)

    skip_ext = set(e.lower() for e in config.get("scan", {}).get("skip_extensions", []))
    skip_names = set(config.get("reorganize", {}).get("skip_files", []))
    from core.scanner import summarize_folder

    count, total = summarize_folder(folder, skip_names, skip_ext)

    return FolderPreview(
        root_id=lib_root_id,
        root_path=str(root_path),
        root_label=root_label,
        device_name=device_name,
        folder_path=rel_folder,
        folder_absolute=str(folder),
        original_name=original,
        normalized_name=normalize_name(original),
        file_count=count,
        total_size=total,
        folder_type=FOLDER_TYPE_COLLECTION,
        is_new=rel_folder not in existing,
    )


def discover_previews_for_root(db: Database, root_id: int, config: dict) -> list[FolderPreview]:
    root_row = next((r for r in db.get_roots() if int(r["id"]) == root_id), None)
    if not root_row:
        return []
    existing = db.get_extraction_paths_for_root(root_id)
    return discover_folder_previews(
        root_id,
        Path(root_row["root_path"]),
        root_row["label"] or root_row["root_path"],
        root_row["device_name"],
        config,
        existing,
    )


def discover_previews_all_roots(db: Database, config: dict) -> list[FolderPreview]:
    previews: list[FolderPreview] = []
    for root in db.get_roots():
        if int(root["enabled"]) != 1:
            continue
        previews.extend(discover_previews_for_root(db, int(root["id"]), config))
    return previews


def apply_folder_previews(db: Database, previews: list[FolderPreview], config: dict) -> list[int]:
    ids: list[int] = []
    for preview in previews:
        ids.append(register_from_preview(db, preview, config))
    return ids


def register_from_preview(db: Database, preview: FolderPreview, config: dict) -> int:
    folder = Path(preview.folder_absolute)
    threshold = float(config.get("name_matching", {}).get("similarity_threshold", 0.85))
    root_path = Path(preview.root_path)

    extraction_id = db.upsert_extraction(
        preview.root_id,
        preview.folder_path,
        preview.original_name,
        preview.normalized_name,
        preview.file_count,
        preview.total_size,
        "online",
        folder_type=preview.folder_type,
    )
    create_or_update_name_match_group(db, extraction_id, threshold)

    skip_ext = set(e.lower() for e in config.get("scan", {}).get("skip_extensions", []))
    skip_names = set(config.get("reorganize", {}).get("skip_files", []))

    for file_path in iter_all_files(folder, skip_names, skip_ext):
        rel_file = str(file_path.relative_to(root_path)).replace("\\", "/")
        try:
            size = file_path.stat().st_size
        except OSError:
            continue
        parent = str(Path(rel_file).parent).replace("\\", "/")
        if parent == ".":
            parent = ""

        db.upsert_media(
            root_id=preview.root_id,
            relative_path=rel_file,
            absolute_path=str(file_path),
            original_name=file_path.name,
            file_size=size,
            file_type=detect_file_type(file_path),
            extraction_id=extraction_id,
            folder_path=parent,
            depth=len(Path(rel_file).parts) - 1,
            mtime=file_mtime_iso(file_path),
        )

    db.log_event(
        "ingested",
        new_path=str(folder),
        extraction_id=extraction_id,
        details=f"approved:{preview.folder_path}",
    )
    return extraction_id


def register_extraction_folder(
    db: Database,
    folder_path: Path | str,
    config: dict,
    root_id: int | None = None,
) -> int:
    """Register one folder (used after approval)."""
    preview = preview_single_folder(db, folder_path, config, root_id)
    return register_from_preview(db, preview, config)
