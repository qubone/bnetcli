"""Utility functions for bnetcli."""
import shutil
import subprocess
from logging import getLogger

logger = getLogger(__name__)


def require_binary(name: str) -> None:
    """Check if a required binary is available in PATH."""
    logger.debug("Checking for required binary: %s", name)
    if not shutil.which(name):
        raise RuntimeError(f"{name} not found in PATH")


def run(cmd: list[str], env: dict | None = None, check: bool = True) -> None:
    """Run a command with optional environment variables."""
    logger.debug("Running command: %s", ' '.join(cmd))
    subprocess.run(cmd, env=env, check=check)
