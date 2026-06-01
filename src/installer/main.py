"""Nuitka-built Windows installer for Media Manager (no Inno Setup)."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
import traceback
import winreg
from dataclasses import dataclass
from pathlib import Path

APP_NAME = "Media Manager"
APP_EXE = "MediaManager.exe"
PUBLISHER = "Dong, Zhexi"
REG_KEY_HKLM = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Media Manager"
REG_KEY_HKCU = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Media Manager"
PAYLOAD_DIR_NAME = "payload"


def is_compiled() -> bool:
    return bool(getattr(sys, "frozen", False) or "__compiled__" in globals())


@dataclass
class InstallArgs:
    VERYSILENT: bool = False
    SUPPRESSMSGBOXES: bool = False
    NORESTART: bool = False
    CLOSEAPPLICATIONS: bool = False
    UNINSTALL: bool = False
    install_dir: str = ""


def default_install_dir() -> Path:
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    return Path(program_files) / APP_NAME


def _runtime_roots() -> list[Path]:
    roots: list[Path] = []
    if not is_compiled():
        return roots

    roots.append(Path(sys.executable).resolve().parent)
    module_dir = Path(__file__).resolve().parent
    roots.extend([module_dir, module_dir.parent])

    onefile_parent = os.environ.get("NUITKA_ONEFILE_PARENT")
    if onefile_parent:
        roots.append(Path(onefile_parent))

    try:
        roots.append(Path(__compiled__.containing_dir))  # type: ignore[name-defined]
    except NameError:
        pass

    unique: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root).casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(root)
    return unique


def resolve_payload_dir() -> Path:
    if is_compiled():
        search_roots = _runtime_roots()
    else:
        search_roots = [Path(__file__).resolve().parents[2] / "dist" / "MediaManager"]

    checked: set[str] = set()
    for root in search_roots:
        for candidate in (root / PAYLOAD_DIR_NAME, root):
            key = str(candidate).casefold()
            if key in checked:
                continue
            checked.add(key)
            if candidate.is_dir() and (candidate / APP_EXE).is_file():
                return candidate

    raise FileNotFoundError(
        f"Installer payload not found (expected {PAYLOAD_DIR_NAME}\\{APP_EXE} in the bundled files)."
    )


def parse_args(argv: list[str] | None = None) -> InstallArgs:
    args = InstallArgs()
    for token in argv if argv is not None else sys.argv[1:]:
        upper = token.upper()
        if upper == "/VERYSILENT":
            args.VERYSILENT = True
        elif upper == "/SUPPRESSMSGBOXES":
            args.SUPPRESSMSGBOXES = True
        elif upper == "/NORESTART":
            args.NORESTART = True
        elif upper == "/CLOSEAPPLICATIONS":
            args.CLOSEAPPLICATIONS = True
        elif upper == "/UNINSTALL":
            args.UNINSTALL = True
        elif upper.startswith("/DIR="):
            args.install_dir = token.split("=", 1)[1]
    return args


def is_silent(args: InstallArgs) -> bool:
    return bool(args.VERYSILENT or args.SUPPRESSMSGBOXES)


def wait_for_app_exit(timeout_sec: int = 120) -> None:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {APP_EXE}"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if APP_EXE.lower() not in result.stdout.lower():
            return
        time.sleep(2)


def copy_payload(payload: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for item in payload.iterdir():
        dest = target / item.name
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)


def _run_powershell(script: str) -> None:
    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        check=False,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def create_shortcuts(install_dir: Path, *, desktop: bool = False) -> None:
    exe = install_dir / APP_EXE
    start_menu = (
        Path(os.environ.get("APPDATA", ""))
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
    )
    start_menu.mkdir(parents=True, exist_ok=True)
    start_link = start_menu / f"{APP_NAME}.lnk"
    script = (
        f'$s = New-Object -ComObject WScript.Shell; '
        f'$l = $s.CreateShortcut("{start_link}"); '
        f'$l.TargetPath = "{exe}"; '
        f'$l.WorkingDirectory = "{install_dir}"; '
        f'$l.Save()'
    )
    _run_powershell(script)
    if desktop:
        desktop_dir = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
        desktop_link = desktop_dir / f"{APP_NAME}.lnk"
        script = (
            f'$s = New-Object -ComObject WScript.Shell; '
            f'$l = $s.CreateShortcut("{desktop_link}"); '
            f'$l.TargetPath = "{exe}"; '
            f'$l.WorkingDirectory = "{install_dir}"; '
            f'$l.Save()'
        )
        _run_powershell(script)


def remove_shortcuts() -> None:
    paths = [
        Path(os.environ.get("APPDATA", ""))
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
        / f"{APP_NAME}.lnk",
        Path(os.environ.get("USERPROFILE", "")) / "Desktop" / f"{APP_NAME}.lnk",
    ]
    for path in paths:
        if path.is_file():
            path.unlink()


def register_uninstall(install_dir: Path, version: str) -> None:
    uninstall_exe = install_dir / "Uninstall.exe"
    installer_source = Path(sys.argv[0]).resolve()
    if not installer_source.is_file():
        installer_source = Path(sys.executable).resolve()
    shutil.copy2(installer_source, uninstall_exe)
    uninstall_cmd = f'"{uninstall_exe}" /UNINSTALL /VERYSILENT /CLOSEAPPLICATIONS'
    values = {
        "DisplayName": APP_NAME,
        "DisplayVersion": version,
        "Publisher": PUBLISHER,
        "InstallLocation": str(install_dir),
        "UninstallString": uninstall_cmd,
        "DisplayIcon": str(install_dir / APP_EXE),
        "NoModify": 1,
        "NoRepair": 1,
    }
    last_error: OSError | None = None
    for hive, subkey in (
        (winreg.HKEY_LOCAL_MACHINE, REG_KEY_HKLM),
        (winreg.HKEY_CURRENT_USER, REG_KEY_HKCU),
    ):
        try:
            with winreg.CreateKey(hive, subkey) as key:
                for name, value in values.items():
                    if isinstance(value, int):
                        winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
                    else:
                        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
            return
        except OSError as e:
            last_error = e
    if last_error is not None:
        raise last_error


def unregister_uninstall() -> None:
    for hive, subkey in (
        (winreg.HKEY_LOCAL_MACHINE, REG_KEY_HKLM),
        (winreg.HKEY_CURRENT_USER, REG_KEY_HKCU),
    ):
        try:
            winreg.DeleteKey(hive, subkey)
        except OSError:
            pass


def read_install_location() -> Path | None:
    for hive, subkey in (
        (winreg.HKEY_LOCAL_MACHINE, REG_KEY_HKLM),
        (winreg.HKEY_CURRENT_USER, REG_KEY_HKCU),
    ):
        try:
            with winreg.OpenKey(hive, subkey) as key:
                value, _ = winreg.QueryValueEx(key, "InstallLocation")
                path = Path(str(value))
                if path.is_dir():
                    return path
        except OSError:
            continue
    return None


def _read_version_from_payload(payload: Path) -> str:
    version_file = payload / "version.txt"
    if version_file.is_file():
        text = version_file.read_text(encoding="utf-8", errors="ignore").strip()
        if text:
            return text
    changelog = payload / "CHANGELOG.md"
    if changelog.is_file():
        match = re.search(r"(\d+\.\d+\.\d+)", changelog.read_text(encoding="utf-8", errors="ignore"))
        if match:
            return match.group(1)
    return "0.0.0"


def confirm_install_dir(default: Path) -> Path | None:
    try:
        import ctypes

        MB_YESNO = 0x04
        MB_ICONINFORMATION = 0x40
        IDYES = 6
        message = (
            f"Install {APP_NAME} to:\n\n{default}\n\n"
            "Click Yes to install, No to cancel."
        )
        result = ctypes.windll.user32.MessageBoxW(0, message, APP_NAME, MB_YESNO | MB_ICONINFORMATION)
        return default if result == IDYES else None
    except OSError:
        return default


def show_error(message: str) -> None:
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, message, APP_NAME, 0x10)
    except OSError:
        print(message, file=sys.stderr)


def install(args: InstallArgs) -> int:
    silent = is_silent(args)
    if args.CLOSEAPPLICATIONS:
        wait_for_app_exit()

    if args.install_dir.strip():
        target = Path(args.install_dir.strip().strip('"'))
    elif silent:
        target = read_install_location() or default_install_dir()
    else:
        chosen = confirm_install_dir(default_install_dir())
        if chosen is None:
            return 1
        target = chosen

    try:
        payload = resolve_payload_dir()
        copy_payload(payload, target)
        version = _read_version_from_payload(payload)
        create_shortcuts(target, desktop=not silent)
        register_uninstall(target, version)
    except OSError as e:
        if not silent:
            show_error(f"Installation failed:\n\n{e}")
        return 1
    except FileNotFoundError as e:
        if not silent:
            show_error(str(e))
        return 1

    if not silent:
        try:
            subprocess.Popen(
                [str(target / APP_EXE)],
                cwd=str(target),
                close_fds=True,
            )
        except OSError as e:
            show_error(f"Installed, but could not start the app:\n\n{e}")
    return 0


def uninstall(args: InstallArgs) -> int:
    silent = is_silent(args)
    if args.CLOSEAPPLICATIONS:
        wait_for_app_exit()

    target = read_install_location()
    if target is None and args.install_dir.strip():
        target = Path(args.install_dir.strip().strip('"'))
    if target is None or not target.is_dir():
        unregister_uninstall()
        remove_shortcuts()
        return 0

    try:
        shutil.rmtree(target)
    except OSError as e:
        if not silent:
            show_error(f"Uninstall failed:\n\n{e}")
        return 1

    unregister_uninstall()
    remove_shortcuts()
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.UNINSTALL:
        return uninstall(args)
    return install(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        show_error(f"Setup failed:\n\n{traceback.format_exc()}")
        raise SystemExit(1)
