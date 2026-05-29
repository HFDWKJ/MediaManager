"""Storage device online/offline detection."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from core.database import Database
from core.device_types import (
    DEVICE_TYPE_HDD,
    DEVICE_TYPE_NAS,
    DEVICE_TYPE_SSD,
    DEVICE_TYPE_UNKNOWN,
)

logger = logging.getLogger(__name__)


def check_path_accessible(path: str | Path) -> bool:
    try:
        p = Path(path)
        return p.exists() and os.access(p, os.R_OK)
    except OSError:
        return False


def detect_device_type(path: Path) -> str:
    """Guess device class from path (user can change later in Library tree)."""
    root = str(path.resolve())
    if root.startswith("\\\\"):
        return DEVICE_TYPE_NAS
    drive = path.drive.upper() if path.drive else ""
    if drive in ("C",):
        return DEVICE_TYPE_SSD
    if drive:
        return DEVICE_TYPE_HDD
    return DEVICE_TYPE_UNKNOWN


def device_identifier(path: Path) -> str:
    try:
        resolved = path.resolve()
        if str(resolved).startswith("\\\\"):
            parts = resolved.parts
            return "\\\\" + "\\".join(parts[:3]) if len(parts) >= 3 else str(resolved)
        return f"{resolved.drive}\\" if resolved.drive else str(resolved.anchor)
    except OSError:
        return str(path)


def refresh_all_device_status(db: Database) -> None:
    roots = db.get_roots()
    devices_seen: dict[int, bool] = {}

    for root in roots:
        device_id = int(root["device_id"])
        root_path = root["root_path"]
        online = check_path_accessible(root_path)
        devices_seen[device_id] = devices_seen.get(device_id, False) or online

        availability = "online" if online else "offline"
        db.update_extraction_availability(int(root["id"]), availability)

    for device in db.get_devices():
        did = int(device["id"])
        is_online = devices_seen.get(did, False)
        db.update_device_online(did, is_online)
        logger.debug("Device %s online=%s", device["name"], is_online)
