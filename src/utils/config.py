"""Application configuration."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from utils.paths import catalog_db_path, config_file_path, is_portable_mode


DEFAULT_CONFIG: dict[str, Any] = {
    "ui": {
        "theme": "dark",
    },
    "update": {
        "check_on_startup": True,
        "github_repo": "HFDWKJ/MediaManager",
        "github_token": "",
        "dismissed_version": "",
    },
    "library_roots": [],
    "scan": {
        "skip_extensions": [".crdownload", ".part", ".tmp", ".aria2"],
        "media_extensions": [
            ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp",
            ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
            ".zip", ".rar", ".7z", ".txt", ".nfo", ".srt",
        ],
        "hash_on_scan": False,
        "hash_chunk_size": 65536,
        "index_plain_subfolders": True,
    },
    "name_matching": {
        "similarity_threshold": 0.85,
        "highlight_exact": True,
        "highlight_similar": True,
    },
    "reorganize": {
        "marker_filename": "media_manager_reorganize.json",
        "write_csv": True,
        "folder_wrapper": "{new_folder_name}",
        "filename_template": "{filetype}_{new_folder_name}_{seq:04d}_{hash8}{ext}",
        "filetype_prefixes": {
            "image": "IMG",
            "video": "VID",
            "other": "NIV",
        },
        "hash_in_filename": "first_8_chars",
        "sequence_rule": "root_files_first_then_subfolders_by_path",
        "delete_empty_subfolders": True,
        "skip_files": [".DS_Store", "Thumbs.db", "desktop.ini"],
        "max_filename_length": 200,
        "preview_required": True,
    },
}


@dataclass
class LibraryRootConfig:
    device_name: str
    device_type: str
    path: str
    label: str = ""


@dataclass
class AppConfig:
    catalog_db: Path
    config_path: Path
    library_roots: list[LibraryRootConfig] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)
    portable: bool = False

    def get(self, *keys: str, default: Any = None) -> Any:
        node: Any = self.raw
        for key in keys:
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node


def config_dir() -> Path:
    return config_file_path().parent


def default_catalog_path() -> Path:
    return catalog_db_path()


def default_config_path() -> Path:
    return config_file_path()


def load_config(path: Path | None = None) -> AppConfig:
    portable = is_portable_mode()
    cfg_path = path or default_config_path()
    data = deepcopy(DEFAULT_CONFIG)

    if cfg_path.exists():
        with open(cfg_path, encoding="utf-8") as f:
            loaded = json.load(f)
            if isinstance(loaded, dict):
                _deep_merge(data, loaded)

    roots: list[LibraryRootConfig] = []
    for item in data.get("library_roots", []):
        if isinstance(item, dict) and item.get("path"):
            roots.append(
                LibraryRootConfig(
                    device_name=item.get("device_name", "Local"),
                    device_type=item.get("device_type", "unknown"),
                    path=str(item["path"]),
                    label=item.get("label", item.get("device_name", "Root")),
                )
            )

    if portable:
        catalog = default_catalog_path()
    elif data.get("catalog_db"):
        catalog = Path(data["catalog_db"])
    else:
        catalog = default_catalog_path()

    return AppConfig(
        catalog_db=catalog,
        config_path=cfg_path,
        library_roots=roots,
        raw=data,
        portable=portable,
    )


def save_config(app_config: AppConfig) -> None:
    data = deepcopy(app_config.raw)
    data["catalog_db"] = str(app_config.catalog_db)
    data["library_roots"] = [
        {
            "device_name": r.device_name,
            "device_type": r.device_type,
            "path": r.path,
            "label": r.label,
        }
        for r in app_config.library_roots
    ]
    app_config.config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(app_config.config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    app_config.raw = data


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> None:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
