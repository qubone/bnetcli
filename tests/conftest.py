"""Fixtures for bnetcli tests."""
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolate_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Isolate HOME for tests so functions that read ~ use tmp_path."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    yield


@pytest.fixture
def run_stub(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """Stub for utils.run that records calls instead of executing them."""
    calls: list[dict] = []

    def _stub(cmd: list[str], env: dict | None = None, check: bool = True) -> None:
        calls.append({"cmd": cmd, "env": env, "check": check})

    monkeypatch.setattr("bnetcli.utils.run", _stub)
    return calls
