"""Proton-related utilities and management functions."""

import re
from logging import getLogger
from pathlib import Path

from .utils import require_binary, run

logger = getLogger(__name__)

PROTON_PATTERN = re.compile(r"GE-Proton(\d+)-(\d+)")

def install(version: str, directory: Path) -> None:
    """Install a specific Proton version using protonup."""
    require_binary("protonup")

    cmd = ["protonup"]

    if version != "latest":
        logger.info("Installing Proton version: %s", version)
        cmd += ["-t", version]
    else:
        logger.info("No version specified, installing latest Proton version")

    cmd += ["-d", str(directory.expanduser())]

    run(cmd)


def remove(version: str) -> None:
    """Remove a specific Proton version using protonup."""
    logger.info("Removing Proton version: %s", version)
    require_binary("protonup")
    run(["protonup", "-r", version])


def remove_installed_versions(proton_dir: Path) -> list[Path]:
    """Remove installed Proton GE versions from the target compatibility directory.

    Only removes directories matching GE-Proton* to avoid removing unrelated files.
    """
    from shutil import rmtree

    removed: list[Path] = []
    proton_dir = proton_dir.expanduser()
    if not proton_dir.exists():
        return removed

    for entry in proton_dir.iterdir():
        if entry.is_dir() and entry.name.startswith("GE-Proton"):
            logger.info("Removing Proton version directory: %s", entry)
            rmtree(entry, ignore_errors=True)
            removed.append(entry)
    return removed


def get_proton_executable(proton_path: Path, version: str) -> Path:
    """Get the path to the Proton executable for a given version."""
    return proton_path.expanduser() / version / "proton"

def detect_latest_proton(proton_dir: Path) -> str | None:
    """Detect latest GE-Proton version installed in proton_dir."""
    proton_dir = proton_dir.expanduser()

    if not proton_dir.exists():
        logger.warning("Proton directory does not exist: %s", proton_dir)
        return None
    logger.debug("Found Proton directory: %s", proton_dir)
    versions = []

    for p in proton_dir.iterdir():
        if not p.is_dir():
            continue

        match = PROTON_PATTERN.match(p.name)

        if match:
            major = int(match.group(1))
            minor = int(match.group(2))
            versions.append((major, minor, p.name))

    if not versions:
        logger.warning("No GE-Proton versions detected in: %s", proton_dir)
        return None

    latest = max(versions)
    logger.info("Detected latest GE-Proton version: %s (version %d-%d)", latest[2], latest[0], latest[1])
    return latest[2]

def resolve_proton_version(
    proton_dir: Path,
    requested_version: str | None
) -> tuple[str, Path]:
    """Resolve which Proton version to use.Returns (version_string, proton_executable_path)."""
    proton_dir = proton_dir.expanduser()

    version: str | None
    if requested_version and requested_version != "auto":
        logger.info("Using user requested Proton version: %s", requested_version)
        version = requested_version
    else:
        logger.info("Auto-detecting latest Proton version...")
        version = detect_latest_proton(proton_dir)

        if version is None:
            # Nothing installed — install latest
            logger.info("No Proton version detected, installing latest...")
            install("latest", proton_dir)
            version = detect_latest_proton(proton_dir)

            if version is None:
                raise RuntimeError("Failed to detect installed Proton version.")

    proton_exe = proton_dir / version / "proton"
    logger.debug("Looking for Proton executable at: %s", proton_exe)

    if not proton_exe.exists():
        raise FileNotFoundError(f"Proton executable not found: {proton_exe}")

    return version, proton_exe

def detect_steam_base_path() -> Path | None:
    """Detect Steam base directory across common Linux installations.Returns base Steam path or None if not found."""
    home = Path.home()
    logger.debug("Home directory: %s", home)

    candidates = [
        home / ".local/share/Steam",  # Native
        home / ".steam/root",         # Symlink variant
        home / ".var/app/com.valvesoftware.Steam/data/Steam",  # Flatpak
    ]

    for path in candidates:
        logger.debug("Checking candidate path: %s", path)
        if path.exists():
            logger.info("Detected Steam path at: %s", path)
            return path
    logger.info("No Steam installation detected in common locations.")
    return None

def ensure_compat_dir(configured_path: Path | None = None) -> Path:
    """Ensure compatibilitytools.d directory exists.

    Priority:
    1. User configured path
    2. Detected Steam installation
    3. Fallback to ~/.local/share/Steam

    """
    if configured_path:
        base = configured_path.expanduser()
        logger.info("Using user configured compatibility tools path: %s", base)
    else:
        detected = detect_steam_base_path()
        if detected:
            base = detected / "compatibilitytools.d"
            logger.info("Using detected Steam path for compatibility tools: %s", base)

        else:
            # No Steam installed — fallback
            base = Path.home() / ".local/share/Steam/compatibilitytools.d"
            logger.warning("No Steam installation detected, using fallback compatibility tools path: %s", base)

    logger.debug("Ensuring compatibility tools directory exists: %s", base)
    base.mkdir(parents=True, exist_ok=True)
    return base
