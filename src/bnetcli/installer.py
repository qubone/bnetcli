"""Functions to download and launch the Battle.net installer."""
from logging import getLogger
from pathlib import Path

import requests

from . import utils
from .environment import prepare_environment

logger = getLogger(__name__)

URL = "https://www.battle.net/download/getInstaller?os=win&installer=Battle.net-Setup.exe"


def download(dest: Path) -> None:
    """Download the Battle.net installer to the specified destination."""
    if dest.exists():
        logger.info("Installer already exists at %s, skipping download", dest)
        return

    dest.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Downloading installer to %s", dest)
    r = requests.get(URL, stream=True, timeout=30)
    r.raise_for_status()

    with dest.open("wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)


def launch_installer(proton: Path, installer: Path, prefix: Path, env_vars: dict):
    """Launch the Battle.net installer using the specified Proton executable and Wine prefix."""
    logger.info("Launching installer %s in prefix %s", installer, prefix)
    env = prepare_environment(prefix, env_vars)
    utils.run([str(proton), "run", str(installer)], env=env)
