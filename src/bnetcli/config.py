"""Configuration management for bnetcli, including loading, saving, and resolving user configurations."""
from dataclasses import dataclass, field
from logging import getLogger
from pathlib import Path

import yaml

logger = getLogger(__name__)

# TODO: Add more STEAM RUNTIME ENVVARS
DEFAULT_CONFIG = {
    "wine_prefix": "/home/qubone/Games/battlenet/pfx",
    "executable": "/home/qubone/Games/battlenet/pfx/drive_c/Program Files (x86)/Battle.net/Battle.net Launcher.exe",
    "proton_path": "/home/qubone/.local/share/Steam/compatibilitytools.d",
    "proton_version": "GE-Proton10-24",
    "installer_path": "/home/qubone/Downloads/Battle.net-Setup.exe",
    "environment": {
        "DXVK_HUD": "0",
        "DXVK_LOG_LEVEL": "warn",
        "DXVK_ASYNC": "1",
        "WINEDLLOVERRIDES": "dxgi=n,b;d3d11=n,b;d3d12=n,b",
        "VKD3D_CONFIG": "use_d3d12",
        "STEAM_COMPAT_CLIENT_INSTALL_PATH": "/home/qubone/.local/share/Steam",
        "STEAM_COMPAT_DATA_PATH": "/home/qubone/Games/battlenet"
    },
}

DEFAULT_CONFIG_AUTO = {
    "wine_prefix": "auto",
    "executable": "auto",
    "proton_path": "auto",
    "proton_version": "auto",
    "installer_path": None,
    "environment": {
        "DXVK_HUD": "0",
        "DXVK_LOG_LEVEL": "warn",
        "DXVK_ASYNC": "1",
        "WINEDLLOVERRIDES": "dxgi=n,b;d3d11=n,b;d3d12=n,b",
        "VKD3D_CONFIG": "use_d3d12"
    },
}

HOME_DIR = Path.home()
CONFIG_FILE_PATH = HOME_DIR / ".config" / "bnetcli" / "config4.yml"
LOG_FILE_PATH = HOME_DIR / ".config" / "bnetcli" / "bnetcli.log"


@dataclass
class BnetConfig:
    """Data class representing the configuration for bnetcli."""

    wine_prefix: Path
    executable: Path
    steam_path: Path
    proton_path: Path
    proton_version: str = "auto"
    installer_path: Path | None = None
    environment: dict[str, str] = field(default_factory=dict)


def load_config(config_file: Path | str | None = None) -> dict:
    """Load configuration from the specified file or create a default config if the file does not exist."""
    path = Path(config_file) if config_file is not None else CONFIG_FILE_PATH
    if not path.exists():
        logger.info("Config file not found at %s, creating default config.", path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as f:
            yaml.dump(DEFAULT_CONFIG, f)
        return DEFAULT_CONFIG

    try:
        with path.open() as f:
            cfg = yaml.safe_load(f)
    except yaml.YAMLError:
        logger.warning("Corrupt config file at %s, recreating default config.", path)
        with path.open("w") as f:
            yaml.dump(DEFAULT_CONFIG, f)
        return DEFAULT_CONFIG

    if cfg is None:
        logger.warning("Empty config file at %s, recreating default config.", path)
        with path.open("w") as f:
            yaml.dump(DEFAULT_CONFIG, f)
        return DEFAULT_CONFIG

    defaults = DEFAULT_CONFIG.copy()
    defaults.update(cfg)
    return defaults


## Auto helper functions
def detect_steam_path() -> Path:
    """Detect Steam installation path across common Linux installations.Returns detected path or None if not found."""
    candidates = [
        HOME_DIR / ".local/share/Steam",
        HOME_DIR / ".steam/steam",
        HOME_DIR / ".var/app/com.valvesoftware.Steam/.local/share/Steam",  # Flatpak
    ]

    for path in candidates:
        if path.exists():
            logger.info("Detected Steam path at %s", path)
            return path

    return candidates[0]

def detect_proton_path() -> Path:
    """Detect Proton compatibility tools path across common Linux installations.

    Returns detected path or None if not found.
    """
    candidates = [
        HOME_DIR / ".local/share/Steam/compatibilitytools.d",
        HOME_DIR / ".steam/steam/compatibilitytools.d",
        HOME_DIR / ".var/app/com.valvesoftware.Steam/.local/share/Steam/compatibilitytools.d",  # Flatpak
        HOME_DIR / ".steam/root/steamapps/common/Proton*"
    ]
    for path in candidates:
        if path.exists():
            logger.info("Detected Proton compatibility tools path at %s", path)
            return path
    return candidates[0]



def default_paths():
    """Determine default paths for Steam, Proton, Wine prefix, and installer based on common Linux configurations."""
    steam = detect_steam_path() or HOME_DIR/ ".local/share/Steam"
    proton = detect_proton_path() or steam / "compatibilitytools.d"

    prefix = HOME_DIR / "Games/battlenet/pfx"

    return {
        "steam_path": steam,
        "wine_prefix": prefix,
        "proton_path": proton,
        "installer_path": HOME_DIR / "Downloads/Battle.net-Setup.exe",
        "executable": prefix / "drive_c/Program Files (x86)/Battle.net/Battle.net Launcher.exe",
    }



def load_config_auto() -> BnetConfig:
    """Load configuration with auto-detection of paths for Steam, Proton, and Wine prefix."""
    path = CONFIG_FILE_PATH

    if not path.exists():
        logger.info("Config file not found at %s, creating default config.", path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w") as f:
            yaml.dump(DEFAULT_CONFIG, f)

        return resolve_config(DEFAULT_CONFIG)

    with path.open() as f:
        cfg = yaml.safe_load(f)

    return resolve_config(cfg)

def detect_latest_proton(proton_dir: Path):
    """Detect the latest installed GE-Proton version in the specified directory."""
    versions = sorted(proton_dir.glob("GE-Proton*"))
    return versions[-1] if versions else None

def build_environment(cfg: BnetConfig, proton_exe: Path) -> dict:
    """Build the environment variables for running Battle.net with Proton.

    Based on the provided configuration and detected Proton executable.
    """
    env = {
        # DXVK / VKD3D tuning
        "DXVK_HUD": "0",
        "DXVK_LOG_LEVEL": "warn",
        "DXVK_ASYNC": "1",

        # Wine overrides
        "WINEDLLOVERRIDES": "dxgi=n,b;d3d11=n,b;d3d12=n,b",

        # VKD3D config
        "VKD3D_CONFIG": "use_d3d12",

        # Proton runtime paths
        "STEAM_COMPAT_CLIENT_INSTALL_PATH": str(cfg.steam_path),
        "STEAM_COMPAT_DATA_PATH": str(cfg.wine_prefix),

        # Important for Proton runtime
        "STEAM_COMPAT_TOOL_PATHS": str(proton_exe.parent),

        # Shader cache
        "STEAM_COMPAT_SHADER_PATH": str(cfg.wine_prefix / "shadercache"),

        # Proton behaviour
        "STEAM_COMPAT_MOUNTS": str(cfg.steam_path),

        # Locale fixes
        "LC_ALL": "C",

        # Prevent Steam runtime conflicts
        "PRESSURE_VESSEL_VERBOSE": "0",

        # Proton Debugging
        "PROTON_LOG": "1",
        "PROTON_LOG_DIR": str(cfg.wine_prefix / "logs"),
    }

    env.update(cfg.environment)

    return env

def resolve_config(user_cfg: dict) -> BnetConfig:
    """Resolve the final configuration by combining user-provided values with auto-detected defaults."""
    defaults = default_paths()

    wine_prefix = (
        defaults["wine_prefix"]
        if user_cfg.get("wine_prefix") == "auto"
        else Path(user_cfg["wine_prefix"]).expanduser()
    )

    return BnetConfig(
        wine_prefix=wine_prefix,
        executable=defaults["executable"],
        steam_path=defaults["steam_path"],
        proton_path=defaults["proton_path"],
        proton_version=user_cfg.get("proton_version", "auto"),
        installer_path=defaults["installer_path"],
        environment=user_cfg.get("environment", {}),
    )
