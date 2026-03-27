from pathlib import Path

from bnetcli import config


def test_resolve_config_with_explicit_values(tmp_path):
    cfg = config.BnetConfig(
        wine_prefix=str(tmp_path / "wp"),
        executable=str(tmp_path / "launcher.exe"),
        proton_path=str(tmp_path / "compat"),
        steam_path=str(tmp_path / "steam"),
        proton_version="GE-ProtonX",
        environment=config.EnvironmentConfig(DXVK_HUD="1"),  # or with defaults
    )

    bcfg = config.BnetConfig.resolve(cfg)
    assert str(bcfg.wine_prefix) == str(Path(cfg.wine_prefix))
    assert bcfg.proton_version == "GE-ProtonX"
    assert bcfg.environment.DXVK_HUD == "1"
