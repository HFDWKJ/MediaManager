"""Storage device type labels and normalization."""

from __future__ import annotations

DEVICE_TYPE_SSD = "ssd"
DEVICE_TYPE_HDD = "hdd"
DEVICE_TYPE_NAS = "nas"
DEVICE_TYPE_DAS = "das"
DEVICE_TYPE_UNKNOWN = "unknown"

DEVICE_TYPE_ORDER: tuple[str, ...] = (
    DEVICE_TYPE_SSD,
    DEVICE_TYPE_HDD,
    DEVICE_TYPE_NAS,
    DEVICE_TYPE_DAS,
    DEVICE_TYPE_UNKNOWN,
)

DEVICE_TYPE_LABELS: dict[str, str] = {
    DEVICE_TYPE_SSD: "SSD",
    DEVICE_TYPE_HDD: "HDD",
    DEVICE_TYPE_NAS: "NAS",
    DEVICE_TYPE_DAS: "DAS",
    DEVICE_TYPE_UNKNOWN: "Other",
}

# ASCII tags — emoji often fail to render in QTreeView on Windows.
DEVICE_TYPE_ICONS: dict[str, str] = {
    DEVICE_TYPE_SSD: "[SSD]",
    DEVICE_TYPE_HDD: "[HDD]",
    DEVICE_TYPE_NAS: "[NAS]",
    DEVICE_TYPE_DAS: "[DAS]",
    DEVICE_TYPE_UNKNOWN: "[?]",
}


def normalize_device_type(value: str | None) -> str:
    key = (value or DEVICE_TYPE_UNKNOWN).strip().lower()
    return key if key in DEVICE_TYPE_LABELS else DEVICE_TYPE_UNKNOWN
