"""Check GitHub releases for application updates."""

from __future__ import annotations

import json
import logging
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from version import __version__

log = logging.getLogger(__name__)

DEFAULT_GITHUB_REPO = "HFDWKJ/MediaManager"
USER_AGENT = f"MediaManager/{__version__}"

INSTALLER_EXE_PATTERN = re.compile(
    r"^MediaManagerSetup[_-]?(\d+(?:\.\d+)+)\.exe$",
    re.IGNORECASE,
)
INSTALLER_ZIP_PATTERN = re.compile(
    r"^MediaManagerSetup[_-]?(\d+(?:\.\d+)+)\.zip$",
    re.IGNORECASE,
)
# Legacy alias
INSTALLER_PATTERN = INSTALLER_EXE_PATTERN
PORTAL_PATTERN = re.compile(
    r"^MediaManagerPortal[_-]?v?(\d+(?:\.\d+)+)\.zip$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ReleaseAsset:
    version: str
    tag_name: str
    name: str
    body: str
    filename: str
    download_url: str
    size_bytes: int
    kind: str  # "installer" | "installer_zip" | "portal"


class UpdateCheckError(Exception):
    """Could not reach GitHub or parse the release response."""


def resolve_github_token(explicit: str | None = None) -> str:
    if explicit and str(explicit).strip():
        return str(explicit).strip()
    for key in ("MEDIA_MANAGER_GITHUB_TOKEN", "GITHUB_TOKEN"):
        value = os.environ.get(key, "").strip()
        if value:
            return value
    return ""


def github_request_headers(
    token: str = "",
    *,
    accept: str = "application/vnd.github+json",
) -> dict[str, str]:
    headers = {
        "Accept": accept,
        "User-Agent": USER_AGENT,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def parse_version(version: str) -> tuple[int, ...]:
    text = version.strip().lstrip("vV")
    parts: list[int] = []
    for segment in re.split(r"[.\-+]", text):
        if not segment:
            continue
        if segment.isdigit():
            parts.append(int(segment))
        else:
            break
    return tuple(parts) if parts else (0,)


def is_newer_version(remote: str, current: str | None = None) -> bool:
    current = current or __version__
    return parse_version(remote) > parse_version(current)


def _api_request(url: str, *, token: str = "", timeout: float = 20.0) -> Any:
    req = urllib.request.Request(
        url,
        headers=github_request_headers(token),
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise UpdateCheckError(f"GitHub API returned HTTP {e.code}") from e
    except urllib.error.URLError as e:
        raise UpdateCheckError(f"Could not reach GitHub: {e.reason}") from e
    except json.JSONDecodeError as e:
        raise UpdateCheckError("Invalid response from GitHub API") from e


def _repo_accessible(repo: str, *, token: str) -> bool:
    return _api_request(f"https://api.github.com/repos/{repo}", token=token) is not None


def _version_from_release(release: dict[str, Any]) -> str:
    tag = str(release.get("tag_name", "")).strip()
    if tag:
        return tag.lstrip("vV")
    name = str(release.get("name", "")).strip()
    return name.lstrip("vV") if name else ""


def _pick_asset(
    assets: list[dict[str, Any]],
    *,
    portable: bool,
) -> tuple[str, str, int, str] | None:
    """Return (filename, url, size, kind) for the best matching asset."""
    if portable:
        patterns: list[tuple[re.Pattern[str], str, int]] = [
            (PORTAL_PATTERN, "portal", 0),
        ]
        fallback_ext = ".zip"
    else:
        # Prefer folder installer zip over onefile exe (fewer Defender false positives).
        patterns = [
            (INSTALLER_ZIP_PATTERN, "installer_zip", 1),
            (INSTALLER_EXE_PATTERN, "installer", 0),
        ]
        fallback_ext = ".exe"

    best: tuple[str, str, int, str, tuple[int, ...], int] | None = None

    for asset in assets:
        if not isinstance(asset, dict):
            continue
        name = str(asset.get("name", ""))
        url = str(asset.get("browser_download_url", ""))
        if not name or not url:
            continue

        matched_kind = ""
        ver = ""
        priority = -1
        for pattern, kind, prio in patterns:
            match = pattern.match(name)
            if match:
                matched_kind = kind
                ver = match.group(1)
                priority = prio
                break
        if not matched_kind:
            if name.lower().endswith(fallback_ext) and "mediamanager" in name.lower():
                matched_kind = patterns[0][1]
                ver = "0.0.0"
                priority = patterns[0][2]
            else:
                continue

        size = int(asset.get("size", 0) or 0)
        candidate = (name, url, size, matched_kind, parse_version(ver), priority)
        if best is None:
            best = candidate
            continue
        if candidate[4] > best[4]:
            best = candidate
        elif candidate[4] == best[4] and candidate[5] > best[5]:
            best = candidate

    if best is None:
        return None
    return best[0], best[1], best[2], best[3]


def fetch_latest_release(
    repo: str = DEFAULT_GITHUB_REPO,
    *,
    portable: bool,
    current_version: str | None = None,
    github_token: str | None = None,
) -> ReleaseAsset | None:
    """Return the newest release asset newer than *current_version*, or None."""
    current_version = current_version or __version__
    repo = repo.strip() or DEFAULT_GITHUB_REPO
    token = resolve_github_token(github_token)
    base = f"https://api.github.com/repos/{repo}"

    release = _api_request(f"{base}/releases/latest", token=token)
    if release is None:
        releases = _api_request(f"{base}/releases", token=token)
        if not isinstance(releases, list):
            if not _repo_accessible(repo, token=token):
                if not token:
                    raise UpdateCheckError(
                        "Cannot access the GitHub repository. "
                        "If the repository is private, set update.github_token in "
                        "config.json or the GITHUB_TOKEN environment variable."
                    )
                raise UpdateCheckError("GitHub repository not found or not accessible.")
            return None
        for item in releases:
            if not isinstance(item, dict):
                continue
            if item.get("draft") or item.get("prerelease"):
                continue
            release = item
            break
        if release is None:
            return None

    if not isinstance(release, dict):
        return None

    version = _version_from_release(release)
    if not version or not is_newer_version(version, current_version):
        return None

    assets = release.get("assets")
    if not isinstance(assets, list):
        return None

    picked = _pick_asset(assets, portable=portable)
    if picked is None:
        log.info("Release %s has no matching %s asset", version, "portal" if portable else "installer")
        return None

    filename, url, size, kind = picked
    return ReleaseAsset(
        version=version,
        tag_name=str(release.get("tag_name", version)),
        name=str(release.get("name", version)),
        body=str(release.get("body", "") or "").strip(),
        filename=filename,
        download_url=url,
        size_bytes=size,
        kind=kind,
    )
