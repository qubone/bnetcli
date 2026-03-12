from pathlib import Path
from typing import Any

import pytest

from bnetcli import wine


def test_create_prefix_when_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, run_stub: list[dict]) -> None:
    prefix = tmp_path / "wineprefix"
    proton = Path("/usr/bin/proton")

    # run_stub fixture patches `bnetcli.utils.run`
    wine.create_prefix(prefix, proton)

    # Directory should be created
    assert prefix.exists()


def test_remove_prefix(tmp_path: Path) -> None:
    prefix = tmp_path / "wineprefix"
    prefix.mkdir()
    (prefix / "file").write_text("x")
    wine.remove_prefix(prefix)
    assert not prefix.exists()


def test_setup_wineprefix_applies_overrides(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prefix = tmp_path / "wineprefix"
    proton = Path("/usr/bin/proton")

    calls: list[Any] = []

    def fake_run(cmd: list[str], env: dict | None = None, check: bool = True) -> None:
        calls.append(cmd)

    monkeypatch.setattr("bnetcli.utils.run", fake_run)

    wine.setup_wineprefix(prefix, proton)
    assert prefix.exists()
    # Should have run at least once for creating prefix and reg add commands
    assert calls
