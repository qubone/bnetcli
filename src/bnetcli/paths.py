"""Functions to get paths to Battle.net files inside a prefix."""
from pathlib import Path


def battlenet_executable(prefix: Path) -> Path:
    """Return path to Battle.net launcher inside a prefix."""
    return (
        prefix
        / "drive_c"
        / "Program Files (x86)"
        / "Battle.net"
        / "Battle.net.exe"
    )

def battlenet_installer_path() -> Path:
    """Return path to Battle.net installer."""
    return Path.home() / "Downloads" / "Battle.net-Setup.exe"

HOME_DIR = Path.home()
CONFIG_FILE_PATH = HOME_DIR / ".config" / "bnetcli" / "config.yml"
LOG_FILE_PATH = HOME_DIR / ".config" / "bnetcli" / "bnetcli.log"
