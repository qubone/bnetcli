from pathlib import Path

from bnetcli import config


def test_resolve_config_with_explicit_values(tmp_path):
    user_cfg = {
        "wine_prefix": str(tmp_path / "wp"),
        "executable": str(tmp_path / "e.exe"),
        "proton_path": str(tmp_path / "compat"),
        "proton_version": "GE-ProtonX",
        "environment": {"A": "B"}
    }

    bcfg = config.resolve_config(user_cfg)
    assert str(bcfg.wine_prefix) == str(Path(user_cfg["wine_prefix"]))
    assert bcfg.proton_version == "GE-ProtonX"
    assert bcfg.environment["A"] == "B"
