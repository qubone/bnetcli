"""Functions to repair common Battle.net prefix issues."""
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


CACHE_DIRS = [
    "Cache",
    "GPUCache",
    "BrowserCache",
    "Code Cache",
]


def clean_battlenet_cache(prefix: Path):
    """Remove Battle.net cache directories."""
    logger.info("Cleaning Battle.net cache directories in prefix: %s", prefix)
    bnet_dir = prefix / "drive_c/Program Files (x86)/Battle.net"

    if not bnet_dir.exists():
        logger.warning("Battle.net directory not found.")
        return

    for cache in CACHE_DIRS:
        path = bnet_dir / cache

        if path.exists():
            logger.info("Removing cache: %s", path)
            shutil.rmtree(path, ignore_errors=True)


def clean_temp(prefix: Path):
    """Clean Wine temp directory."""
    logger.info("Cleaning Wine temp directory in prefix: %s", prefix)
    temp = prefix / "drive_c/users/steamuser/Temp"

    if temp.exists():
        logger.info("Cleaning Wine temp directory")
        shutil.rmtree(temp, ignore_errors=True)


def repair_prefix(prefix: Path):
    """Repair common Battle.net prefix issues."""
    logger.info("Repairing Battle.net prefix...")

    if not prefix.exists():
        logger.error("Wine prefix does not exist")
        return

    clean_battlenet_cache(prefix)
    clean_temp(prefix)

    logger.info("Repair complete.")
