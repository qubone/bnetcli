from pathlib import Path

import pytest
from click.testing import CliRunner

from bnetcli import cli


def test_install_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    runner: CliRunner = CliRunner()

    # Stub out system checks and other side effects
    monkeypatch.setattr("bnetcli.system.print_system_summary", lambda: None)
    monkeypatch.setattr("bnetcli.config.load_config", lambda path=None: {
        "proton_path": None,
        "wine_prefix": "/tmp/prefix",
        "installer_path": "/tmp/installer.exe",
        "environment": {}
    })
    monkeypatch.setattr("bnetcli.proton.ensure_compat_dir", lambda p: Path("/tmp/compat"))
    proton_path = Path("/tmp/compat/GE-Proton10-24/proton")
    monkeypatch.setattr(
        "bnetcli.proton.resolve_proton_version",
        lambda d, v: ("GE-Proton10-24", proton_path),
    )
    monkeypatch.setattr("bnetcli.wine.create_prefix", lambda prefix, proton: None)
    monkeypatch.setattr("bnetcli.installer.download", lambda dest: None)
    monkeypatch.setattr("bnetcli.installer.launch_installer", lambda *a, **k: None)

    result = runner.invoke(cli.cli, ["install", "--dry-run"])
    assert result.exit_code == 0
    assert "Would download installer" in result.output


def test_repair_prefix(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner: CliRunner = CliRunner()
    d = tmp_path / "prefix"
    d.mkdir()
    monkeypatch.setattr("bnetcli.config.load_config", lambda path=None: {"wine_prefix": str(d)})

    result = runner.invoke(cli.cli, ["repair-prefix"])
    assert result.exit_code == 0
