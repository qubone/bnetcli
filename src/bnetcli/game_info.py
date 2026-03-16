"""Game information utilities for installed Blizzard games."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

KNOWN_BLIZZARD_GAME_PATTERNS = {
    "World of Warcraft": ["world of warcraft", "wow"],
    "Diablo IV": ["diablo iv", "diablo 4", "diabloiv"],
    "Diablo III": ["diablo iii", "diablo 3", "diabloiii"],
    "Overwatch 2": ["overwatch 2", "overwatch2", "overwatch"],
    "Hearthstone": ["hearthstone"],
    "StarCraft II": ["starcraft ii", "starcraft2", "starcraft 2"],
    "Heroes of the Storm": ["heroes of the storm", "heroes"],
    "Call of Duty": ["call of duty"],
}


def _calculate_directory_size(path: Path) -> tuple[int, int]:
    """Return (total_bytes, total_files) under path."""
    total = 0
    file_count = 0
    try:
        for entry in path.rglob("*"):
            if entry.is_file():
                file_count += 1
                try:
                    total += entry.stat().st_size
                except OSError:
                    continue
    except OSError:
        return 0, 0
    return total, file_count


class GameInfo:
    """Information about an installed game that can be printed and summarized."""

    def __init__(self, name: str, path: Path, disk_usage_bytes: int = 0, file_count: int = 0):
        """Initialize GameInfo with name, path, disk usage in bytes, and file count."""
        self.name = name
        self.path = path
        self.disk_usage_bytes = disk_usage_bytes
        self.file_count = file_count

    @classmethod
    def from_detected_path(cls, name: str, path: Path) -> "GameInfo":
        """Create GameInfo by calculating disk usage and file count for the given path."""
        total_bytes, files = _calculate_directory_size(path)
        return cls(name=name, path=path, disk_usage_bytes=total_bytes, file_count=files)

    def pretty_bytes(self) -> str:
        """Return a human-readable string for the disk usage."""
        size: float = float(self.disk_usage_bytes)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}PB"

    def __str__(self) -> str:
        """Return a human-readable string representation of the GameInfo."""
        return f"{self.name}: {self.path} ({self.pretty_bytes()}, {self.file_count} files)"


def find_installed_blizzard_games(prefix: Path) -> dict[str, GameInfo]:
    """Search for installed Blizzard games inside a wine prefix drive_c."""
    prefix = prefix.expanduser()
    if not prefix.exists():
        logger.warning("Prefix directory not found: %s", prefix)
        return {}

    installed: dict[str, GameInfo] = {}
    for path in prefix.rglob("*"):
        if not path.exists():
            continue
        name = path.name.lower()
        for game_name, clues in KNOWN_BLIZZARD_GAME_PATTERNS.items():
            if game_name in installed:
                logger.info("Already found %s, skipping further checks for this game.", game_name)
                continue
            for clue in clues:
                if clue in name or clue in str(path).lower():
                    installed[game_name] = GameInfo.from_detected_path(game_name, path)
                    break
    return installed
