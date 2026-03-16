from pathlib import Path

import pytest
from click.testing import CliRunner

from bnetcli import cli, config


def test_integration_cli_dry_run_install_and_start(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = CliRunner()

    exe_path = tmp_path / "prefix" / "drive_c" / "Program Files (x86)" / "Battle.net" / "Battle.net Launcher.exe"
    cfg = {
        "wine_prefix": str(tmp_path / "prefix"),
        "executable": str(exe_path),
        "proton_path": str(tmp_path / "compat"),
        "installer_path": str(tmp_path / "installer.exe"),
        "environment": {},
    }

    monkeypatch.setattr("bnetcli.config.load_config", lambda p=None: cfg)
    monkeypatch.setattr("bnetcli.proton.ensure_compat_dir", lambda p: Path(cfg["proton_path"]))  # type: ignore[arg-type]
    def fake_resolve_proton_version(d, v):
        return "GE-Proton10-24", Path(cfg["proton_path"]) / "GE-Proton10-24" / "proton"  # ty:ignore[invalid-argument-type]

    monkeypatch.setattr("bnetcli.proton.resolve_proton_version", fake_resolve_proton_version)
    monkeypatch.setattr("bnetcli.wine.create_prefix", lambda prefix, proton: prefix.mkdir(parents=True, exist_ok=True))
    monkeypatch.setattr("bnetcli.installer.download", lambda dest: None)
    monkeypatch.setattr("bnetcli.installer.launch_installer", lambda *args, **kwargs: None)
    monkeypatch.setattr("bnetcli.system.print_system_summary", lambda: None)
    monkeypatch.setattr("bnetcli.utils.run", lambda *args, **kwargs: None)

    result = runner.invoke(cli.cli, ["install", "--dry-run"])
    assert result.exit_code == 0
    assert "Would download installer" in result.output

    result = runner.invoke(cli.cli, ["start", "--disable-browser", "--start-minimized"])
    assert result.exit_code == 0
    assert "Using Proton version" in result.output


def test_load_config_missing_and_corrupt(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yml"
    assert not config_path.exists()

    cfg = config.load_config(config_path)
    assert cfg["wine_prefix"]
    assert config_path.exists()

    config_path.write_text("not: valid: yaml: -")
    cfg2 = config.load_config(config_path)
    assert cfg2["wine_prefix"]


def test_start_missing_steam(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = CliRunner()
    cfg = {
        "wine_prefix": str(tmp_path / "prefix"),
        "executable": str(tmp_path / "launcher.exe"),
        "proton_path": str(tmp_path / "compat"),
        "environment": {},
    }

    monkeypatch.setattr("bnetcli.config.load_config", lambda path=None: cfg)
    monkeypatch.setattr("bnetcli.proton.detect_steam_base_path", lambda: None)
    monkeypatch.setattr("bnetcli.proton.ensure_compat_dir", lambda p: tmp_path / "compat")
    monkeypatch.setattr("bnetcli.utils.run", lambda *a, **k: None)

    result = runner.invoke(cli.cli, ["start"])
    assert result.exit_code == 0
    assert "Steam installation not detected" in result.output
