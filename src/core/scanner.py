"""File scanning, hashing, and type detection."""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

logger = logging.getLogger(__name__)

EXTRACTION_PATTERN = re.compile(r"^\[(.+)\]$")

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"}
VIDEO_EXT = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"}
ARCHIVE_EXT = {".zip", ".rar", ".7z", ".tar", ".gz"}
DOC_EXT = {".txt", ".nfo", ".pdf", ".doc", ".docx", ".srt", ".ass"}

# Reorganize filename prefixes (3 letters)
REORG_PREFIX_IMAGE = "IMG"
REORG_PREFIX_VIDEO = "VID"
REORG_PREFIX_OTHER = "NIV"  # not image or video


def parse_extraction_folder_name(dir_name: str) -> str | None:
    """Return inner name if folder matches [Original Name] pattern."""
    m = EXTRACTION_PATTERN.match(dir_name.strip())
    return m.group(1).strip() if m else None


def calculate_hash(file_path: Path, chunk_size: int = 65536) -> str | None:
    try:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                h.update(chunk)
        return h.hexdigest()
    except OSError as e:
        logger.warning("Hash failed for %s: %s", file_path, e)
        return None


def detect_file_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in IMAGE_EXT:
        return "IMAGE"
    if ext in VIDEO_EXT:
        return "VIDEO"
    if ext in ARCHIVE_EXT:
        return "ARCHIVE"
    if ext in DOC_EXT:
        return "DOC"
    return "OTHER"


def reorganize_file_prefix(
    path: Path, overrides: dict[str, str] | None = None
) -> str:
    """Three-letter prefix for reorganize filenames: IMG, VID, or NIV."""
    cfg = overrides or {}
    ext = path.suffix.lower()
    if ext in IMAGE_EXT:
        return str(cfg.get("image", REORG_PREFIX_IMAGE))
    if ext in VIDEO_EXT:
        return str(cfg.get("video", REORG_PREFIX_VIDEO))
    return str(cfg.get("other", REORG_PREFIX_OTHER))


def file_mtime_iso(path: Path) -> str:
    try:
        ts = path.stat().st_mtime
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    except OSError:
        return ""


def should_skip_file(path: Path, skip_names: set[str], skip_extensions: set[str]) -> bool:
    if path.name in skip_names:
        return True
    if path.suffix.lower() in skip_extensions:
        return True
    return False


def iter_all_files(root: Path, skip_names: set[str], skip_extensions: set[str]) -> Iterator[Path]:
    try:
        for p in root.rglob("*"):
            if p.is_file() and not should_skip_file(p, skip_names, skip_extensions):
                yield p
    except OSError as e:
        logger.warning("Cannot walk %s: %s", root, e)


def discover_extraction_folders(root: Path) -> Iterator[tuple[Path, str, str]]:
    """Yield (folder_path, original_name, relative_folder_path) for [Name] dirs."""
    seen: set[str] = set()

    try:
        # Library root itself may be [Original Name]
        if root.is_dir():
            inner = parse_extraction_folder_name(root.name)
            if inner:
                key = "."
                if key not in seen:
                    seen.add(key)
                    yield root, inner, key

        for p in root.rglob("*"):
            if not p.is_dir():
                continue
            inner = parse_extraction_folder_name(p.name)
            if inner:
                rel = str(p.relative_to(root)).replace("\\", "/")
                if rel not in seen:
                    seen.add(rel)
                    yield p, inner, rel
    except OSError as e:
        logger.warning("Cannot discover extractions in %s: %s", root, e)


def discover_plain_subfolders(root: Path, max_depth: int = 2) -> Iterator[tuple[Path, str, str]]:
    """Yield direct (or shallow) subfolders without [brackets] for fallback indexing."""
    try:
        for p in sorted(root.iterdir()):
            if not p.is_dir() or p.name.startswith("."):
                continue
            if parse_extraction_folder_name(p.name):
                continue  # already handled by bracket discovery
            rel = str(p.relative_to(root)).replace("\\", "/")
            yield p, p.name, rel
        if max_depth >= 2:
            for parent in sorted(root.iterdir()):
                if not parent.is_dir():
                    continue
                for child in sorted(parent.iterdir()):
                    if not child.is_dir() or child.name.startswith("."):
                        continue
                    if parse_extraction_folder_name(child.name):
                        continue
                    rel = str(child.relative_to(root)).replace("\\", "/")
                    yield child, child.name, rel
    except OSError as e:
        logger.warning("Cannot discover plain subfolders in %s: %s", root, e)


def build_file_sequence(root: Path, skip_names: set[str], skip_extensions: set[str]) -> list[Path]:
    """Root files first, then subfolders sorted by path."""
    root_files: list[Path] = []
    sub_files: list[tuple[str, Path]] = []

    for p in iter_all_files(root, skip_names, skip_extensions):
        rel = p.relative_to(root)
        if len(rel.parts) == 1:
            root_files.append(p)
        else:
            sub_files.append((str(rel).replace("\\", "/"), p))

    root_files.sort(key=lambda x: x.name.lower())
    sub_files.sort(key=lambda x: x[0].lower())
    return root_files + [p for _, p in sub_files]


def summarize_folder(folder: Path, skip_names: set[str], skip_extensions: set[str]) -> tuple[int, int]:
    count = 0
    total = 0
    for f in iter_all_files(folder, skip_names, skip_extensions):
        try:
            total += f.stat().st_size
            count += 1
        except OSError:
            pass
    return count, total
