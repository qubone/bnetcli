from pathlib import Path
from typing import Any

import pytest

from bnetcli import environment


def test_get_vulkan_icds_user_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Create ~/.local/share/vulkan/icd.d with a json file
    home = Path.home()
    user_icd = home / ".local" / "share" / "vulkan" / "icd.d"
    user_icd.mkdir(parents=True)
    f = user_icd / "test.json"
    f.write_text("{}")

    icds = environment.get_vulkan_icds()
    assert str(f) in icds


def test_prepare_environment(tmp_path: Path) -> None:
    prefix = tmp_path / "prefix"
    env: dict[str, str] = {"FOO": "bar"}

    prepared: dict[str, Any] = environment.prepare_environment(prefix, env)
    assert prepared.get("WINEPREFIX") == str(prefix)
    assert prepared.get("FOO") == "bar"
    assert "VK_ICD_FILENAMES" in prepared
