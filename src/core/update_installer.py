"""Download and apply Media Manager updates."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable

from core.update_checker import ReleaseAsset, github_request_headers
from utils.paths import application_root, is_portable_mode
from utils.runtime import is_compiled

log = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int], None]


class UpdateInstallError(Exception):
    pass


def update_download_dir() -> Path:
    path = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "MediaManager" / "Updates"
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_windows_security_block(exc: BaseException) -> bool:
    return getattr(exc, "winerror", None) in (225, 226)


def format_install_error(
    exc: BaseException,
    *,
    installer_path: Path | None = None,
) -> str:
    code = getattr(exc, "winerror", None) or getattr(exc, "errno", None)
    if code == 740:
        return (
            "The update installer requires administrator approval.\n\n"
            "When Windows shows the UAC prompt, choose Yes to continue."
        )
    if code in (5, 1223):
        return "Update cancelled — administrator approval was not granted."
    if is_windows_security_block(exc):
        path_line = f"\n\nInstaller file:\n{installer_path}" if installer_path else ""
        return (
            "Windows blocked the update installer (antivirus / Smart App Control).\n\n"
            "Add a Defender exclusion for the folder above, allow the file in "
            "Protection history, or download the installer from GitHub Releases."
            + path_line
        )
    return f"Could not start installer: {exc}"


def download_release_asset(
    asset: ReleaseAsset,
    dest_dir: Path,
    *,
    progress: ProgressCallback | None = None,
    timeout: float = 300.0,
    github_token: str = "",
) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / asset.filename
    req = urllib.request.Request(
        asset.download_url,
        headers=github_request_headers(github_token, accept="application/octet-stream"),
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            total = int(resp.headers.get("Content-Length", asset.size_bytes) or 0)
            downloaded = 0
            chunk_size = 256 * 1024
            with open(dest_path, "wb") as out:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    out.write(chunk)
                    downloaded += len(chunk)
                    if progress:
                        progress(downloaded, total if total > 0 else downloaded)
    except OSError as e:
        raise UpdateInstallError(f"Download failed: {e}") from e

    if not dest_path.is_file() or dest_path.stat().st_size == 0:
        raise UpdateInstallError("Downloaded file is missing or empty")
    return dest_path


def apply_update(package_path: Path, asset: ReleaseAsset) -> None:
    if asset.kind == "portal" or is_portable_mode():
        _apply_portable_update(package_path, application_root())
        return
    _apply_installer_update(package_path)


def _quote_windows_cmd_arg(value: str) -> str:
    if not value or any(c in value for c in ' \t"'):
        return '"' + value.replace('"', r"\"") + '"'
    return value


def _shell_execute_installer(installer_path: Path, params: list[str]) -> None:
    """Launch the setup exe with UAC elevation (required by --windows-uac-admin)."""
    import ctypes

    param_str = " ".join(_quote_windows_cmd_arg(p) for p in params)
    result = ctypes.windll.shell32.ShellExecuteW(  # type: ignore[attr-defined]
        None,
        "runas",
        str(installer_path),
        param_str,
        None,
        1,  # SW_SHOWNORMAL
    )
    if result <= 32:
        raise OSError(result, "ShellExecute failed", str(installer_path))


def _apply_installer_update(installer_path: Path) -> None:
    if not installer_path.is_file():
        raise UpdateInstallError(f"Installer not found: {installer_path}")
    params = ["/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CLOSEAPPLICATIONS"]
    install_dir = application_root()
    if install_dir.is_dir():
        params.append(f'/DIR={install_dir}')
    try:
        if sys.platform == "win32":
            _shell_execute_installer(installer_path, params)
        else:
            subprocess.Popen(
                [str(installer_path), *params],
                close_fds=True,
            )
    except OSError as e:
        raise UpdateInstallError(
            format_install_error(e, installer_path=installer_path)
        ) from e


def _apply_portable_update(zip_path: Path, app_root: Path) -> None:
    if not zip_path.is_file():
        raise UpdateInstallError(f"Package not found: {zip_path}")

    staging = Path(tempfile.mkdtemp(prefix="mm_update_"))
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(staging)
    except (OSError, zipfile.BadZipFile) as e:
        raise UpdateInstallError(f"Could not extract update package: {e}") from e

    payload = _find_payload_root(staging)
    updater = _write_portable_updater_script(payload, app_root)
    try:
        os.startfile(str(updater))  # type: ignore[attr-defined]
    except OSError as e:
        raise UpdateInstallError(f"Could not launch updater: {e}") from e


def _find_payload_root(staging: Path) -> Path:
    if (staging / "MediaManager.exe").is_file():
        return staging
    for child in staging.iterdir():
        if child.is_dir() and (child / "MediaManager.exe").is_file():
            return child
    raise UpdateInstallError("Update package does not contain MediaManager.exe")


def _write_portable_updater_script(payload_dir: Path, app_root: Path) -> Path:
    script_dir = Path(tempfile.mkdtemp(prefix="mm_updater_"))
    cmd_path = script_dir / "apply_media_manager_update.cmd"
    exe_name = "MediaManager.exe"
    lines = [
        "@echo off",
        "setlocal",
        f'set "TARGET={app_root}"',
        f'set "SOURCE={payload_dir}"',
        f'set "EXE={exe_name}"',
        "echo Waiting for Media Manager to close...",
        ":wait_loop",
        'tasklist /FI "IMAGENAME eq %EXE%" 2>nul | find /I "%EXE%" >nul',
        "if not errorlevel 1 (",
        "  timeout /t 2 /nobreak >nul",
        "  goto wait_loop",
        ")",
        'robocopy "%SOURCE%" "%TARGET%" /E /XD data /XF portable.marker /NFL /NDL /NJH /NJS /nc /ns /np',
        "if %ERRORLEVEL% GEQ 8 exit /b %ERRORLEVEL%",
        'start "" "%TARGET%\\%EXE%"',
        "endlocal",
        "del \"%~f0\"",
    ]
    cmd_path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    return cmd_path


def can_apply_in_app_update() -> bool:
    return is_compiled()
