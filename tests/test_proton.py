from pathlib import Path
from typing import Any

import pytest

from bnetcli import proton


def test_get_proton_executable(tmp_path: Path) -> None:
    base = tmp_path / "compat"
    path = proton.get_proton_executable(base, "GE-Proton10-24")
    assert str(path).endswith("GE-Proton10-24/proton")


def test_detect_latest_proton(tmp_path: Path) -> None:
    base = tmp_path / "compat"
    (base / "GE-Proton10-24").mkdir(parents=True)
    (base / "GE-Proton11-3").mkdir(parents=True)
    (base / "other").mkdir()

    latest = proton.detect_latest_proton(base)
    assert latest == "GE-Proton11-3"


def test_resolve_proton_version_requested(tmp_path: Path) -> None:
    base = tmp_path / "compat"
    vdir = base / "GE-Proton10-24"
    vdir.mkdir(parents=True)
    (vdir / "proton").write_text("")

    version, exe = proton.resolve_proton_version(base, "GE-Proton10-24")
    assert version == "GE-Proton10-24"
    assert exe.exists()


def test_resolve_proton_version_auto_installs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base = tmp_path / "compat"

    # Simulate install creating a proton dir
    def fake_install(version: str, directory: Path) -> None:
        d = Path(directory) / "GE-Proton99-1"
        d.mkdir(parents=True, exist_ok=True)
        (d / "proton").write_text("")

    monkeypatch.setattr(proton, "install", fake_install)
    # Force detect_latest_proton to return None first, then real value after install
    orig_detect = proton.detect_latest_proton

    def detect_after(d: Path) -> Any:
        vals = list(Path(d).glob("GE-Proton*"))
        return orig_detect(d) if vals else None

    monkeypatch.setattr(proton, "detect_latest_proton", detect_after)

    version, exe = proton.resolve_proton_version(base, "auto")
    assert version == "GE-Proton99-1"
    assert exe.exists()
