"""Configuration management for bnetcli, including loading, saving, and resolving user configurations."""
from logging import getLogger
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, ValidationError

from .paths import CONFIG_FILE_PATH, HOME_DIR, battlenet_executable, battlenet_installer_path

logger = getLogger(__name__)


class EnvironmentConfig(BaseModel):
    """Default environment variables for running Battle.net with Proton.

    Users can override these in their config file.
    """

    DXVK_HUD: str = "0"
    DXVK_LOG_LEVEL: str = "warn"
    DXVK_ASYNC: str = "1"
    WINEDLLOVERRIDES: str = "dxgi=n,b;d3d11=n,b;d3d12=n,b"
    VKD3D_CONFIG: str = "use_d3d12"


class BnetConfig(BaseModel):
    """Configuration for bnetcli, including paths to Wine prefix, Battle.net executable, Steam installation.

    Proton tools, and environment variables.
    """

    wine_prefix: Path | None = None
    executable: Path | None = None
    steam_path: Path | None = None
    proton_path: Path | None = None
    proton_version: str = "auto"
    installer_path: Path | None = None
    environment: EnvironmentConfig = Field(default_factory=EnvironmentConfig)

    class Config:
        """Pydantic configuration to allow arbitrary types like Path and to enable model dumping."""

        arbitrary_types_allowed = True

    def resolve(self) -> "BnetConfig":
        """Resolve the final configuration by filling in any missing values with auto-detected defaults."""
        defaults = default_paths()

        return BnetConfig(
            wine_prefix=self.wine_prefix or defaults["wine_prefix"],
            executable=self.executable or defaults["executable"],
            steam_path=self.steam_path or defaults["steam_path"],
            proton_path=self.proton_path or defaults["proton_path"],
            proton_version=self.proton_version,
            installer_path=self.installer_path or defaults["installer_path"],
            environment=self.environment,
        )


def load_config(config_file: Path | None = None) -> BnetConfig:
    """Load configuration from a YAML file, or return defaults if the file doesn't exist."""
    path = config_file or CONFIG_FILE_PATH

    if not path.exists():
        logger.warning("Config file not found at %s, generating default configuration", path)
        return BnetConfig().resolve()

    try:
        with path.open() as f:
            logger.info("Loading configuration from %s", path)
            data = yaml.safe_load(f) or {}
    except (yaml.YAMLError, ValidationError) as e:
        logger.warning("Invalid config file %s: %s. Using defaults.", path, e)
        return BnetConfig().resolve()

    return BnetConfig(**data).resolve()


def generate_auto_config() -> BnetConfig:
    """Generate a configuration based on auto-detected paths without relying on an existing config file."""
    defaults = default_paths()

    proton_dir = defaults["proton_path"]
    latest = detect_latest_proton(proton_dir)

    return BnetConfig(
        wine_prefix=defaults["wine_prefix"],
        executable=defaults["executable"],
        steam_path=defaults["steam_path"],
        proton_path=defaults["proton_path"],
        proton_version=latest.name if latest else "auto",
        installer_path=defaults["installer_path"],
    )

def save_config(cfg: BnetConfig, path: Path):
    """Save the given configuration to a YAML file at the specified path."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w") as f:
        yaml.safe_dump(cfg.model_dump(mode="json"), f)

# TODO: Add more STEAM RUNTIME ENVVARS
DEFAULT_CONFIG = {
    "wine_prefix": None,
    "executable": None,
    "steam_path": None,
    "proton_path": None,
    "proton_version": "auto",
    "installer_path": None,
    "environment": {
        "DXVK_HUD": "0",
        "DXVK_LOG_LEVEL": "warn",
        "DXVK_ASYNC": "1",
        "WINEDLLOVERRIDES": "dxgi=n,b;d3d11=    n,b;d3d12=n,b",
        "VKD3D_CONFIG": "use_d3d12",
    },
}


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
    logger.info("Determining default paths for Steam, Proton, Wine prefix, and installer...")
    steam = detect_steam_path() or HOME_DIR/ ".local/share/Steam"
    logger.debug("Default Steam path set to: %s", steam)
    proton = detect_proton_path() or steam / "compatibilitytools.d"
    logger.debug("Default Proton path set to: %s", proton)
    prefix = HOME_DIR / "Games" / "battlenet" / "pfx"
    logger.debug("Default Wine prefix set to: %s", prefix)

    return {
        "steam_path": steam,
        "wine_prefix": prefix,
        "proton_path": proton,
        "installer_path": battlenet_installer_path(),
        "executable": battlenet_executable(prefix),
    }


def detect_latest_proton(proton_dir: Path):
    """Detect the latest installed GE-Proton version in the specified directory."""
    versions = sorted(proton_dir.glob("GE-Proton*"))
    return versions[-1] if versions else None

def build_environment(cfg: BnetConfig, proton_exe: Path) -> dict:
    """Build the environment variables for running Battle.net with Proton.

    Based on the provided configuration and detected Proton executable.
    """
    assert cfg.wine_prefix is not None
    assert cfg.steam_path is not None
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
