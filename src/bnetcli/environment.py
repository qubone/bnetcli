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


def validate_proton_environment(env: dict) -> None:
    """Validate required Proton environment variables and path values."""
    required = ["WINEPREFIX", "STEAM_COMPAT_DATA_PATH", "STEAM_COMPAT_CLIENT_INSTALL_PATH"]
    missing = [k for k in required if not env.get(k)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    # Optionally validate paths if needed; the caller can verify existence separately.
    return


def prepare_environment(prefix: Path, env_vars: dict, steam_path: Path | None = None) -> dict:
    """Prepare environment variables for running Battle.net with Proton in the specified prefix."""
    logger.debug("Preparing environment for prefix: %s", prefix)
    env = os.environ.copy()
    env["WINEPREFIX"] = str(prefix)

    if steam_path is not None:
        env["STEAM_COMPAT_CLIENT_INSTALL_PATH"] = str(steam_path)

    env["STEAM_COMPAT_DATA_PATH"] = str(prefix)

    for k, v in env_vars.items():
        env.setdefault(k, str(v))

    env.setdefault("STEAM_COMPAT_CLIENT_INSTALL_PATH", str(Path.home() / ".local/share/Steam"))
    env.setdefault("VK_ICD_FILENAMES", get_vulkan_icds())

    validate_proton_environment(env)
    logger.debug(
        "Prepared environment variables: %s",
        {k: env.get(k) for k in ["WINEPREFIX", "STEAM_COMPAT_DATA_PATH", "STEAM_COMPAT_CLIENT_INSTALL_PATH"]})
    return env
