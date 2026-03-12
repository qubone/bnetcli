from pathlib import Path
from typing import Any

import pytest
import requests

from bnetcli import installer


class DummyResponse:
    """Simple dummy response object mimicking `requests.Response` for tests."""

    def __init__(self, data: bytes = b"abc") -> None:
        """Initialize with optional byte payload."""
        self._data = data

    def raise_for_status(self) -> None:
        """Mimic successful HTTP status by doing nothing."""
        return None

    def iter_content(self, size: int):
        """Yield the stored payload in chunks (single chunk for tests)."""
        yield self._data


def test_download_existing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dest = tmp_path / "Downloads" / "Battle.net-Setup.exe"
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"x")

    # Should not call requests.get
    called: dict = {}

    def fake_get(url: str, stream: bool, timeout: int) -> DummyResponse:
        called["hit"] = True
        return DummyResponse()

    monkeypatch.setattr(requests, "get", fake_get)

    installer.download(dest)
    assert not called


def test_download_new(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dest = tmp_path / "Downloads" / "Battle.net-Setup.exe"
    dest.parent.mkdir(parents=True)

    def fake_get(url: str, stream: bool, timeout: int) -> DummyResponse:
        return DummyResponse(b"data")

    monkeypatch.setattr(requests, "get", fake_get)

    installer.download(dest)
    assert dest.exists()
    assert dest.read_bytes() == b"data"


def test_launch_installer_calls_run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[Any] = []

    def fake_run(cmd: list[str], env: dict | None = None, check: bool = True) -> None:
        calls.append((cmd, env, check))

    # Patch the underlying utils.run used by installer
    monkeypatch.setattr("bnetcli.utils.run", fake_run)
    monkeypatch.setattr("bnetcli.environment.prepare_environment", lambda prefix, env: {"WINEPREFIX": str(prefix)})

    installer.launch_installer(Path("/usr/bin/proton"), tmp_path / "inst.exe", tmp_path / "prefix", {"A": "1"})
    assert calls
