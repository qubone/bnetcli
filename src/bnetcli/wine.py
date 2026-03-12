"""Wine prefix management for bnetcli."""

import os
import shutil
from logging import getLogger
from pathlib import Path

from . import utils

logger = getLogger(__name__)

def create_prefix(prefix: Path, proton: Path) -> None:
    """Create a Wine prefix using the specified Proton executable."""
    logger.debug("Creating Wine prefix at %s using Proton executable %s", prefix, proton)
    if prefix.exists():
        logger.info("Wine prefix already exists at %s", prefix)
        return

    prefix.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["WINEPREFIX"] = str(prefix)
    logger.debug("Setting WINEPREFIX to %s", prefix)
    utils.run([str(proton), "run", "cmd", "/c", "exit"], env=env)


def remove_prefix(prefix: Path) -> None:
    """Remove the Wine prefix directory."""
    if prefix.exists():
        logger.debug("Removing Wine prefix at %s", prefix)
        shutil.rmtree(prefix)

def setup_wineprefix(wine_prefix: Path, proton_exe: Path) -> None:
    """Create Wine prefix if missing and apply recommended DLL overrides."""
    if wine_prefix.is_dir():
        logger.info("Wine prefix already exists at %s", wine_prefix)
        return

    wine_prefix.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["WINEPREFIX"] = str(wine_prefix)

    logger.info("Creating new Wine prefix at %s...", wine_prefix)
    utils.run([str(proton_exe), "run", "cmd", "/c", "exit"], env=env, check=True)

    # Set DLL overrides for DXVK and vkd3d
    overrides = {"dxgi": "n,b", "d3d11": "n,b", "d3d12": "n,b"}
    for dll, val in overrides.items():
        logger.info("Setting DLL override for %s: %s", dll, val)
        utils.run(
            [str(proton_exe), "run", "reg", "add", "HKCU\\Software\\Wine\\DllOverrides", "/v", dll, "/d", val, "/f"],
            env=env,
        )
