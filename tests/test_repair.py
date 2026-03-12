from pathlib import Path

import pytest

from bnetcli import repair


def test_clean_battlenet_cache(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    prefix = tmp_path / "prefix"
    bnet = prefix / "drive_c" / "Program Files (x86)" / "Battle.net"
    cache_dir = bnet / "Cache"
    cache_dir.mkdir(parents=True)
    (cache_dir / "tmpfile").write_text("x")

    repair.clean_battlenet_cache(prefix)

    assert not cache_dir.exists()


def test_clean_temp(tmp_path: Path) -> None:
    prefix = tmp_path / "prefix"
    temp = prefix / "drive_c" / "users" / "steamuser" / "Temp"
    temp.mkdir(parents=True)
    (temp / "t").write_text("1")

    repair.clean_temp(prefix)

    assert not temp.exists()


def test_repair_prefix_missing(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    prefix = tmp_path / "notexists"
    # Should log error but not raise
    repair.repair_prefix(prefix)
