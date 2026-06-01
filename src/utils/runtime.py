"""Detect packaged (compiled) application runs."""

from __future__ import annotations

import sys


def is_compiled() -> bool:
    """True when running as a packaged app (PyInstaller, Nuitka, etc.)."""
    if getattr(sys, "frozen", False):
        return True
    try:
        __compiled__  # noqa: F821
        return True
    except NameError:
        return False
