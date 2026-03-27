from pathlib import Path

import pytest
from click.testing import CliRunner

from bnetcli import cli
from bnetcli.config import BnetConfig, EnvironmentConfig


def test_install_non_dry_run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = CliRunner()

    # Stub out system checks and side effects
    monkeypatch.setattr("bnetcli.system.print_system_summary", lambda: None)

    cfg = BnetConfig(
        proton_path=tmp_path / "compat",
        wine_prefix=tmp_path / "prefix",
        steam_path=tmp_path / "steam",
        installer_path=tmp_path / "inst.exe",
        environment=EnvironmentConfig(),
    )

    monkeypatch.setattr("bnetcli.config.load_config", lambda path=None: cfg)

    # Ensure proton exe exists
    proton_exe = Path(str(cfg.proton_path)) / "GE-Proton10-24" / "proton"
    proton_exe.parent.mkdir(parents=True)
    proton_exe.write_text("")

    monkeypatch.setattr(
        "bnetcli.proton.ensure_compat_dir",
        lambda p: Path(str(cfg.proton_path)),
    )
    monkeypatch.setattr("bnetcli.proton.resolve_proton_version", lambda d, v: ("GE-Proton10-24", proton_exe))

    calls = {"download": 0, "launch": 0}

    def fake_download(dest):
        calls["download"] += 1

    def fake_launch(proton, installer_path, prefix, env):
        calls["launch"] += 1

    monkeypatch.setattr("bnetcli.installer.download", fake_download)
    monkeypatch.setattr("bnetcli.installer.launch_installer", fake_launch)
    monkeypatch.setattr("bnetcli.wine.create_prefix", lambda prefix, proton: None)

    result = runner.invoke(cli.cli, ["install"])
    assert result.exit_code == 0
    assert calls["download"] == 1
    assert calls["launch"] == 1
