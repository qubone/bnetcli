import shutil
import subprocess
from typing import Any

import pytest

from bnetcli import utils


def test_require_binary_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/fake")
    # Should not raise
    utils.require_binary("fake")


def test_require_binary_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError):
        utils.require_binary("missing")


def test_run_calls_subprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[Any] = []

    def fake_run(cmd: list[str], env: dict | None = None, check: bool = True) -> None:
        calls.append((cmd, env, check))

    monkeypatch.setattr(subprocess, "run", fake_run)

    utils.run(["echo", "hi"], env={"A": "1"}, check=False)

    assert calls
    assert calls[0][0] == ["echo", "hi"]
    assert calls[0][1] == {"A": "1"}
    assert calls[0][2] is False
