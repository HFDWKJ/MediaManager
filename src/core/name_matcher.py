"""Tier 1: [Original Name] soft matching."""

from __future__ import annotations

import logging
import re

from rapidfuzz import fuzz

from core.database import Database

logger = logging.getLogger(__name__)

COPY_SUFFIX = re.compile(r"\s*\(\d+\)\s*$")


def normalize_name(name: str) -> str:
    s = name.strip().lower()
    s = COPY_SUFFIX.sub("", s)
    s = re.sub(r"[^\w\s-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def safe_new_folder_name(name: str, max_len: int = 80) -> str:
    invalid = '<>:"/\\|?*'
    s = "".join(c for c in name if c not in invalid).strip()
    s = s[:max_len].rstrip(". ")
    return s or "Unnamed"


def folder_name_on_disk(name: str) -> str:
    """Plain folder name on disk (no brackets)."""
    from core.names import strip_bracket_wrapper
    return safe_new_folder_name(strip_bracket_wrapper(name))


def find_exact_matches(db: Database, normalized: str, exclude_id: int | None) -> list[int]:
    rows = db.get_extractions_by_normalized_name(normalized, exclude_id)
    return [int(r["id"]) for r in rows]


def find_similar_matches(
    db: Database, normalized: str, exclude_id: int | None, threshold: float = 0.85
) -> list[tuple[int, float]]:
    results: list[tuple[int, float]] = []
    for eid, other in db.get_all_normalized_names(exclude_id):
        if other == normalized:
            continue
        score = fuzz.ratio(normalized, other) / 100.0
        if score >= threshold:
            results.append((eid, score))
    results.sort(key=lambda x: -x[1])
    return results


def create_or_update_name_match_group(db: Database, extraction_id: int, threshold: float = 0.85) -> int | None:
    row = db.get_extraction(extraction_id)
    if not row:
        return None

    normalized = row["normalized_name"]
    exact_ids = find_exact_matches(db, normalized, extraction_id)
    similar = find_similar_matches(db, normalized, extraction_id, threshold)

    member_ids = list(dict.fromkeys(exact_ids + [eid for eid, _ in similar]))
    if not member_ids:
        return None

    all_ids = [extraction_id] + [i for i in member_ids if i != extraction_id]
    match_type = "exact" if exact_ids else "similar"
    score = None if match_type == "exact" else (similar[0][1] if similar else None)

    group_id = db.create_name_match_group(normalized, match_type, all_ids, score)
    logger.info(
        "Name match %s for '%s': %d members (group %d)",
        match_type, row["original_name"], len(all_ids), group_id,
    )
    return group_id


def suggest_new_folder_name(db: Database, extraction_id: int) -> str:
    from core.names import format_display_name

    row = db.get_extraction(extraction_id)
    if not row:
        return "Unnamed"
    return safe_new_folder_name(format_display_name(row["original_name"]))
