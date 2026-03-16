from pathlib import Path

from bnetcli import game_info


def test_calculate_directory_size_counts_files_and_bytes(tmp_path: Path) -> None:
    base = tmp_path / "drive_c" / "Program Files" / "Game"
    base.mkdir(parents=True)
    (base / "a.txt").write_bytes(b"abc")
    (base / "b.bin").write_bytes(b"0123456789")
    total, count = game_info._calculate_directory_size(base)
    assert count == 2
    assert total == 3 + 10


def test_calculate_directory_size_ignores_missing_file(tmp_path: Path) -> None:
    base = tmp_path / "game"
    base.mkdir()
    file_path = base / "missing.bin"
    with open(file_path, "wb") as f:
        f.write(b"hello")
    # simulate missing by removing file before stat evaluation
    file_path.unlink()
    total, count = game_info._calculate_directory_size(base)
    assert count == 0
    assert total == 0


def test_game_info_pretty_bytes_formats_units(tmp_path: Path) -> None:
    info = game_info.GameInfo("Test", tmp_path, disk_usage_bytes=1024 * 1024 * 2 + 512, file_count=5)
    assert info.pretty_bytes().endswith("MB")
    assert "MB" in info.pretty_bytes()


def test_game_info_str_contains_data(tmp_path: Path) -> None:
    info = game_info.GameInfo("Example", tmp_path, disk_usage_bytes=1234, file_count=3)
    txt = str(info)
    assert "Example" in txt
    assert "files" in txt


def test_find_installed_blizzard_games_returns_empty_for_nonexistent_prefix(tmp_path: Path) -> None:
    result = game_info.find_installed_blizzard_games(tmp_path / "does-not-exist")
    assert result == {}


def test_find_installed_blizzard_games_detects_by_pattern(tmp_path: Path) -> None:
    base = tmp_path / "prefix" / "drive_c" / "Program Files (x86)" / "Diablo IV"
    base.mkdir(parents=True)
    (base / "diablo.exe").write_bytes(b"x")

    result = game_info.find_installed_blizzard_games(tmp_path)
    assert "Diablo IV" in result
    info = result["Diablo IV"]
    assert isinstance(info, game_info.GameInfo)
    assert info.name == "Diablo IV"
    assert info.file_count >= 1
