"""Unique 5-character Face UIDs (A–Z and 0–9)."""

from __future__ import annotations

import secrets
import string

UID_LENGTH = 5
UID_ALPHABET = string.ascii_uppercase + string.digits


def generate_uid_candidate() -> str:
    return "".join(secrets.choice(UID_ALPHABET) for _ in range(UID_LENGTH))


def generate_unique_uid(existing: set[str], *, max_attempts: int = 5000) -> str:
    """Return a UID not present in `existing` (case-sensitive)."""
    taken = {u.upper() for u in existing}
    for _ in range(max_attempts):
        candidate = generate_uid_candidate()
        if candidate not in taken:
            return candidate
    raise RuntimeError(f"Could not allocate a unique {UID_LENGTH}-character UID")
