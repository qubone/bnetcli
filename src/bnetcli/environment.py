"""Functions to prepare the environment for running Battle.net with Proton."""
import os
from logging import getLogger
from pathlib import Path

logger = getLogger(__name__)

def get_vulkan_icds() -> str:
    """Get Vulkan ICD file paths from common system locations."""
    paths = []
    for base in [
        Path("/usr/share/vulkan/icd.d"),
        Path.home() / ".local/share/vulkan/icd.d",
    ]:
        if base.exists():
            paths += list(base.glob("*.json"))

    logger.debug("Found Vulkan ICD files: %s", paths)
    return ":".join(str(p) for p in paths)


def prepare_environment(prefix: Path, env_vars: dict) -> dict:
    """Prepare environment variables for running Battle.net with Proton in the specified prefix."""
    logger.debug("Preparing environment for prefix: %s", prefix)
    env = os.environ.copy()
    env["WINEPREFIX"] = str(prefix)

    for k, v in env_vars.items():
        env.setdefault(k, str(v))

    env.setdefault("VK_ICD_FILENAMES", get_vulkan_icds())
    logger.debug("Prepared environment variables: %s", {k: env[k] for k in env_vars.keys()})
    return env
