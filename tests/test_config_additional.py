from pathlib import Path
from typing import Any

import pytest
import yaml

from bnetcli import config


def test_load_config_writes_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg_path = tmp_path / "cfg" / "config.yml"
    # Ensure HOME_DIR used by config functions is isolated
    monkeypatch.setattr(config, "HOME_DIR", tmp_path)
    # Use explicit path to avoid writing to real home
    result = config.load_config(cfg_path)
    assert cfg_path.exists()
    assert isinstance(result, dict)
    # File contents should be YAML and include expected keys
    with cfg_path.open() as f:
        data = yaml.safe_load(f)
    assert "wine_prefix" in data


def test_detect_steam_and_proton_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_home = tmp_path
    monkeypatch.setattr(config, "HOME_DIR", fake_home)

    steam_dir = fake_home / ".local" / "share" / "Steam"
    proton_dir = fake_home / ".local" / "share" / "Steam" / "compatibilitytools.d"
    proton_dir.mkdir(parents=True)
    steam_dir.mkdir(parents=True, exist_ok=True)

    s = config.detect_steam_path()
    p = config.detect_proton_path()

    assert s.exists()
    assert p.exists()


def test_default_paths_use_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(config, "HOME_DIR", tmp_path)
    d = config.default_paths()
    assert d["steam_path"].exists() is False
    assert "wine_prefix" in d


def test_build_environment_and_resolve_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Prepare a minimal user_cfg
    user_cfg = {"wine_prefix": "auto", "environment": {"FOO": "bar"}}
    bcfg = config.resolve_config(user_cfg)
    # Create a fake proton exe parent
    proton_exe = tmp_path / "compat" / "GE-Proton10-24" / "proton"
    proton_exe.parent.mkdir(parents=True)
    env: dict[str, Any] = config.build_environment(bcfg, proton_exe)
    assert env["FOO"] == "bar"
    assert "PROTON_LOG_DIR" in env
