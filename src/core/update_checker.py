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

INSTALLER_PATTERN = re.compile(
    r"^MediaManagerSetup[_-]?(\d+(?:\.\d+)+)\.exe$",
    re.IGNORECASE,
)
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
    kind: str  # "installer" | "portal"


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
) -> tuple[str, str, int] | None:
    pattern = PORTAL_PATTERN if portable else INSTALLER_PATTERN
    fallback_ext = ".zip" if portable else ".exe"
    best: tuple[str, str, int, tuple[int, ...]] | None = None

    for asset in assets:
        if not isinstance(asset, dict):
            continue
        name = str(asset.get("name", ""))
        url = str(asset.get("browser_download_url", ""))
        if not name or not url:
            continue
        match = pattern.match(name)
        if match:
            ver = match.group(1)
        elif name.lower().endswith(fallback_ext) and "mediamanager" in name.lower():
            ver = "0.0.0"
        else:
            continue
        size = int(asset.get("size", 0) or 0)
        candidate = (name, url, size, parse_version(ver))
        if best is None or candidate[3] > best[3]:
            best = candidate

    if best is None:
        return None
    return best[0], best[1], best[2]


def _release_to_asset(
    release: dict[str, Any],
    *,
    portable: bool,
    current_version: str,
) -> ReleaseAsset | None:
    version = _version_from_release(release)
    if not version or not is_newer_version(version, current_version):
        return None
    assets = release.get("assets")
    if not isinstance(assets, list):
        return None
    picked = _pick_asset(assets, portable=portable)
    if picked is None:
        return None
    filename, url, size = picked
    return ReleaseAsset(
        version=version,
        tag_name=str(release.get("tag_name", version)),
        name=str(release.get("name", version)),
        body=str(release.get("body", "") or "").strip(),
        filename=filename,
        download_url=url,
        size_bytes=size,
        kind="portal" if portable else "installer",
    )


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

    best: ReleaseAsset | None = None
    best_ver: tuple[int, ...] = ()

    for item in releases:
        if not isinstance(item, dict) or item.get("draft"):
            continue
        # Skip prerelease builds (e.g. develop branch v0.0.4.1 zip installer).
        if item.get("prerelease"):
            continue
        candidate = _release_to_asset(item, portable=portable, current_version=current_version)
        if candidate is None:
            continue
        ver_tuple = parse_version(candidate.version)
        if best is None or ver_tuple > best_ver:
            best = candidate
            best_ver = ver_tuple

    if best is None:
        log.info("No newer release with a matching %s asset", "portal" if portable else "installer")
    return best
