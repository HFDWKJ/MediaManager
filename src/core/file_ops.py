"""File operations and Explorer integration."""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def show_in_explorer(file_path: str | Path) -> bool:
    path = Path(file_path)
    if not path.exists():
        return False
    try:
        if path.is_file():
            subprocess.run(
                ["explorer", "/select,", str(path.resolve())],
                check=False,
            )
        else:
            os.startfile(str(path.resolve()))
        return True
    except OSError as e:
        logger.warning("Explorer open failed: %s", e)
        return False


def generate_sidecar_json(file_path: Path, metadata: dict, force: bool = False) -> bool:
    sidecar = file_path.with_suffix(file_path.suffix + ".json")
    if sidecar.exists() and not force:
        return False
    try:
        with open(sidecar, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        return True
    except OSError as e:
        logger.warning("Sidecar write failed: %s", e)
        return False
