"""Folder name display and normalization helpers."""

from __future__ import annotations

import re

BRACKET_WRAP = re.compile(r"^\[(.+)\]$")


def strip_bracket_wrapper(name: str) -> str:
    """Remove outer [brackets] for display and new folder names."""
    s = name.strip()
    m = BRACKET_WRAP.match(s)
    return m.group(1).strip() if m else s


def format_display_name(name: str) -> str:
    """Plain display name without brackets."""
    return strip_bracket_wrapper(name)
