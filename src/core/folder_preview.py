"""Discover folders for user approval before writing to the database."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.database import FOLDER_TYPE_COLLECTION
from core.device_manager import check_path_accessible
from core.names import format_display_name
from core.name_matcher import normalize_name
from core.scanner import (
    discover_extraction_folders,
    discover_plain_subfolders,
    summarize_folder,
)


@dataclass
class FolderPreview:
    root_id: int
    root_path: str
    root_label: str
    device_name: str
    folder_path: str
    folder_absolute: str
    original_name: str
    normalized_name: str
    file_count: int
    total_size: int
    folder_type: str = FOLDER_TYPE_COLLECTION
    is_new: bool = True
    existing_id: int | None = None

    @property
    def display_name(self) -> str:
        return format_display_name(self.original_name)

    @property
    def size_mb(self) -> float:
        return self.total_size / 1024 / 1024

    @property
    def display_path(self) -> str:
        """Relative path for UI (brackets stripped from each segment)."""
        parts = self.folder_path.replace("\\", "/").split("/")
        return "/".join(format_display_name(p) for p in parts if p and p != ".")


def discover_folder_previews(
    root_id: int,
    root_path: Path,
    root_label: str,
    device_name: str,
    config: dict,
    existing_paths: set[str],
) -> list[FolderPreview]:
    """Scan disk and return previews only (no database writes). Default type is Collections."""
    if not check_path_accessible(root_path):
        return []

    skip_ext = set(e.lower() for e in config.get("scan", {}).get("skip_extensions", []))
    skip_names = set(config.get("reorganize", {}).get("skip_files", []))
    previews: list[FolderPreview] = []
    seen_paths: set[str] = set()

    def add_preview(folder: Path, display_name: str, rel: str) -> None:
        rel_key = rel.replace("\\", "/")
        if rel_key in seen_paths:
            return
        seen_paths.add(rel_key)
        count, total = summarize_folder(folder, skip_names, skip_ext)
        previews.append(
            FolderPreview(
                root_id=root_id,
                root_path=str(root_path),
                root_label=root_label,
                device_name=device_name,
                folder_path=rel_key,
                folder_absolute=str(folder.resolve()),
                original_name=display_name,
                normalized_name=normalize_name(display_name),
                file_count=count,
                total_size=total,
                folder_type=FOLDER_TYPE_COLLECTION,
                is_new=rel_key not in existing_paths,
            )
        )

    scan_cfg = config.get("scan", {})
    index_plain = scan_cfg.get("index_plain_subfolders", True)

    # Direct children of library root
    try:
        for child in sorted(root_path.iterdir()):
            if not child.is_dir() or child.name.startswith("."):
                continue
            rel = str(child.relative_to(root_path)).replace("\\", "/")
            add_preview(child, format_display_name(child.name), rel)
    except OSError:
        pass

    # Nested folders (any name — brackets are not used for type)
    for folder, _original, rel in discover_extraction_folders(root_path):
        add_preview(folder, format_display_name(folder.name), rel)

    if index_plain:
        for folder, original, rel in discover_plain_subfolders(root_path):
            add_preview(folder, format_display_name(original), rel)

    return previews
