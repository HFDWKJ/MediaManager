"""Light scan ingestion pipeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from core.database import Database, FOLDER_TYPE_ROOT
from core.device_manager import check_path_accessible
from core.name_matcher import create_or_update_name_match_group, normalize_name
from core.names import format_display_name
from core.scanner import (
    detect_file_type,
    discover_extraction_folders,
    discover_plain_subfolders,
    file_mtime_iso,
    iter_all_files,
    summarize_folder,
)

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int, str, bool], None]


@dataclass
class ScanResult:
    extractions: int = 0
    files: int = 0
    matches: int = 0
    skipped: bool = False


def scan_root(
    db: Database,
    root_id: int,
    config: dict,
    progress: ProgressCallback | None = None,
) -> ScanResult:
    roots = db.get_roots()
    root_row = next((r for r in roots if int(r["id"]) == root_id), None)
    if not root_row:
        return ScanResult(skipped=True)

    root_path = Path(root_row["root_path"])
    if not check_path_accessible(root_path):
        db.update_extraction_availability(root_id, "offline")
        return ScanResult(skipped=True)

    skip_ext = set(e.lower() for e in config.get("scan", {}).get("skip_extensions", []))
    skip_names = set(config.get("reorganize", {}).get("skip_files", []))
    threshold = float(config.get("name_matching", {}).get("similarity_threshold", 0.85))

    result = ScanResult()
    extraction_map: dict[Path, int] = {}

    def _index_folder(folder: Path, rel: str, display_name: str) -> None:
        nonlocal result
        count, total = summarize_folder(folder, skip_names, skip_ext)
        norm = normalize_name(display_name)
        eid = db.upsert_extraction(
            root_id, rel, display_name, norm, count, total, "online",
            folder_type=FOLDER_TYPE_ROOT,
        )
        extraction_map[folder.resolve()] = eid
        result.extractions += 1
        gid = create_or_update_name_match_group(db, eid, threshold)
        if gid:
            result.matches += 1
        if progress:
            progress(result.extractions, 0, rel, gid is not None)

    seen_rels: set[str] = set()

    try:
        for child in sorted(root_path.iterdir()):
            if not child.is_dir() or child.name.startswith("."):
                continue
            rel = str(child.relative_to(root_path)).replace("\\", "/")
            if rel not in seen_rels:
                seen_rels.add(rel)
                _index_folder(child, rel, format_display_name(child.name))
    except OSError:
        pass

    for folder, _original, rel in discover_extraction_folders(root_path):
        if rel.replace("\\", "/") not in seen_rels:
            seen_rels.add(rel.replace("\\", "/"))
            _index_folder(folder, rel, format_display_name(folder.name))

    scan_cfg = config.get("scan", {})
    if scan_cfg.get("index_plain_subfolders", True):
        for folder, original, rel in discover_plain_subfolders(root_path):
            rel_key = rel.replace("\\", "/")
            if rel_key in seen_rels:
                continue
            seen_rels.add(rel_key)
            _index_folder(folder, rel_key, format_display_name(original))

    # Index files (light — no hash)
    all_files = list(iter_all_files(root_path, skip_names, skip_ext))
    total_files = len(all_files)
    for i, file_path in enumerate(all_files, 1):
        rel = str(file_path.relative_to(root_path)).replace("\\", "/")
        extraction_id = _find_extraction_id(file_path, extraction_map)
        try:
            size = file_path.stat().st_size
        except OSError:
            continue

        ftype = detect_file_type(file_path)
        if file_path.suffix.lower() == ".rar":
            status = "indexed"
        else:
            status = "indexed"

        db.upsert_media(
            root_id=root_id,
            relative_path=rel,
            absolute_path=str(file_path),
            original_name=file_path.name,
            file_size=size,
            file_type=ftype,
            extraction_id=extraction_id,
            folder_path=str(Path(rel).parent).replace("\\", "/") if "/" in rel or "\\" in rel else "",
            depth=len(Path(rel).parts) - 1,
            mtime=file_mtime_iso(file_path),
            status=status,
        )
        result.files += 1
        if progress and i % 50 == 0:
            progress(i, total_files, file_path.name, False)

    db.update_root_scan(root_id, result.extractions)
    if progress:
        progress(total_files, total_files, "Done", False)
    return result


def _find_extraction_id(file_path: Path, extraction_map: dict[Path, int]) -> int | None:
    resolved = file_path.resolve()
    best: Path | None = None
    for ext_dir in extraction_map:
        try:
            resolved.relative_to(ext_dir)
            if best is None or len(ext_dir.parts) > len(best.parts):
                best = ext_dir
        except ValueError:
            continue
    return extraction_map.get(best) if best else None


def scan_all_enabled_roots(
    db: Database,
    config: dict,
    progress: ProgressCallback | None = None,
) -> list[ScanResult]:
    results = []
    for root in db.get_roots(enabled_only=True):
        if int(root["enabled"]) != 1:
            continue
        results.append(scan_root(db, int(root["id"]), config, progress))
    return results
