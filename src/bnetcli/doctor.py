"""Functions to perform system diagnostics for Battle.net on Linux."""
import os
import platform
import shutil
import subprocess
from logging import getLogger
from pathlib import Path

import click

from .config import load_config
from .environment import get_vulkan_icds
from .proton import (
    detect_latest_proton,
    detect_steam_base_path,
    ensure_compat_dir,
)
from .system import check_vulkan, detect_gpu

logger = getLogger(__name__)

# ------------------------
# Utility helpers
# ------------------------

def _binary_exists(name: str) -> bool:
    logger.debug("Checking for binary: %s", name)
    return shutil.which(name) is not None


def _run_quiet(cmd: list[str]) -> tuple[int, str]:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        return result.returncode, result.stdout.strip()
    except FileNotFoundError:
        return 127, ""


# ------------------------
# System Checks
# ------------------------

def _check_32bit_support():
    logger.debug("Checking for 32-bit library support")
    if platform.machine() != "x86_64":
        click.secho("System is not x86_64 (Proton requires 64-bit Linux)", fg="red")
        return

    if Path("/lib/ld-linux.so.2").exists() or Path("/lib32").exists():
        click.secho("32-bit libraries appear to be installed", fg="green")
    else:
        click.secho("32-bit libraries may be missing", fg="yellow")


def _detect_mesa_version():
    logger.debug("Detecting Mesa version")
    if not _binary_exists("glxinfo"):
        click.secho("glxinfo not available (cannot detect Mesa version)", fg="yellow")
        return

    _, output = _run_quiet(["glxinfo"])

    for line in output.splitlines():
        if "OpenGL version string" in line:
            click.echo(line)
            break


def _detect_session_type():
    logger.debug("Detecting display session type")
    session = os.environ.get("XDG_SESSION_TYPE", "unknown")

    if session == "wayland":
        click.secho("Running under Wayland session", fg="cyan")
    elif session == "x11":
        click.secho("Running under X11 session", fg="cyan")
    else:
        click.secho("Session type unknown", fg="yellow")


def _check_flatpak_steam(steam_path: Path | None):
    logger.debug("Checking for Flatpak Steam installation")
    if steam_path and "com.valvesoftware.Steam" in str(steam_path):
        click.secho(
            "Steam Flatpak detected (ensure proper filesystem access)",
            fg="yellow",
        )


# ------------------------
# Main Diagnostic Entry
# ------------------------


def check_graphics():
    """Check graphics configuration and report potential issues."""
    logger.debug("Checking graphics configuration")
     # ---- Vulkan ----
    click.echo("\n[Vulkan]")
    if check_vulkan():
        click.secho("Vulkan loader OK (vulkaninfo succeeded)", fg="green")
    else:
        click.secho("Vulkan loader present but failed", fg="red")

    icds = get_vulkan_icds()
    if icds:
        click.secho("Vulkan ICD files detected", fg="green")
    else:
        click.secho("No Vulkan ICD files detected", fg="red")

    # ---- GPU ----
    click.echo("\n[GPU]")

    if detect_gpu() == "unknown":
        click.secho("GPU vendor could not be detected", fg="yellow")

    if "NVIDIA" in detect_gpu():
        click.secho("Detected NVIDIA GPU", fg="cyan")
    elif "AMD" in detect_gpu() or "ATI" in detect_gpu():
        click.secho("Detected AMD GPU", fg="cyan")
    elif "Intel" in detect_gpu():
        click.secho("Detected Intel GPU", fg="cyan")
    else:
        click.secho("GPU type unknown", fg="yellow")

    # ---- Mesa ----
    click.echo("\n[Graphics Stack]")
    _detect_mesa_version()

    # ---- 32-bit ----
    click.echo("\n[32-bit Support]")
    _check_32bit_support()

    # ---- Session ----
    click.echo("\n[Display Session]")
    _detect_session_type()

def run_diagnostics():
    """Run a series of diagnostics to check system compatibility for running Battle.net with Proton."""
    logger.debug("Running system diagnostics")
    click.echo("=== bnetcli Advanced System Diagnostics ===\n")

    cfg = load_config()

    # ---- Architecture ----
    click.echo(f"System architecture: {platform.machine()}")

    # ---- Steam Detection ----
    steam_path = detect_steam_base_path()
    if steam_path:
        click.secho(f"Steam detected at: {steam_path}", fg="green")
    else:
        click.secho("Steam not detected (fallback mode active)", fg="yellow")

    _check_flatpak_steam(steam_path)

    compat_dir = ensure_compat_dir(None)
    click.echo(f"Compatibility tools directory: {compat_dir}")

    # ---- ProtonUp ----
    if _binary_exists("protonup"):
        click.secho("protonup found", fg="green")
    else:
        click.secho("protonup NOT found", fg="red")

    # ---- Proton Versions ----
    latest = detect_latest_proton(compat_dir)
    if latest:
        click.secho(f"Installed Proton version detected: {latest}", fg="green")
    else:
        click.secho("No GE-Proton version detected", fg="yellow")

    check_graphics()

    # ---- Wine Prefix ----
    click.echo("\n[Wine Prefix]")
    prefix = Path(cfg["wine_prefix"]).expanduser()
    if prefix.exists():
        click.secho(f"Wine prefix exists: {prefix}", fg="green")
    else:
        click.secho(f"Wine prefix missing: {prefix}", fg="yellow")

    # ---- Battle.net ----
    battlenet_exe = (
        prefix
        / "drive_c"
        / "Program Files (x86)"
        / "Battle.net"
        / "Battle.net.exe"
    )

    if battlenet_exe.exists():
        click.secho("Battle.net executable found", fg="green")
    else:
        click.secho("Battle.net executable NOT found", fg="yellow")

    click.echo("\n=== Diagnostics Complete ===")
