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


def test_uninstall_removes_battle_net_data(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner: CliRunner = CliRunner()
    prefix = tmp_path / "prefix"
    prefix.mkdir(parents=True)
    installer_path = tmp_path / "Battle.net-Setup.exe"
    installer_path.write_text("data")
    proton_dir = tmp_path / "compat"
    proton_dir.mkdir(parents=True)
    (proton_dir / "GE-Proton10-24").mkdir(parents=True)

    cfg = {
        "wine_prefix": str(prefix),
        "installer_path": str(installer_path),
        "proton_path": str(proton_dir),
    }
    monkeypatch.setattr("bnetcli.config.load_config", lambda p=None: cfg)

    result = runner.invoke(cli.cli, ["uninstall"], input="y\ny\n")
    assert result.exit_code == 0
    assert not prefix.exists()
    assert not installer_path.exists()
    assert not (proton_dir / "GE-Proton10-24").exists()


def test_uninstall_then_install_behaves_like_fresh(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner: CliRunner = CliRunner()
    prefix = tmp_path / "prefix"
    installer_path = tmp_path / "Battle.net-Setup.exe"
    proton_dir = tmp_path / "compat"
    cfg = {
        "wine_prefix": str(prefix),
        "installer_path": str(installer_path),
        "proton_path": str(proton_dir),
        "environment": {},
    }

    monkeypatch.setattr("bnetcli.config.load_config", lambda p=None: cfg)
    monkeypatch.setattr("bnetcli.proton.ensure_compat_dir", lambda path: proton_dir)
    def fake_resolve_proton_version(d, v):
        return "GE-Proton10-24", Path(proton_dir / "GE-Proton10-24" / "proton")

    monkeypatch.setattr("bnetcli.proton.resolve_proton_version", fake_resolve_proton_version)
    monkeypatch.setattr("bnetcli.wine.create_prefix", lambda p, e: p.mkdir(parents=True, exist_ok=True))
    monkeypatch.setattr("bnetcli.installer.download", lambda d: None)
    monkeypatch.setattr("bnetcli.installer.launch_installer", lambda *a, **k: None)
    monkeypatch.setattr("bnetcli.system.print_system_summary", lambda: None)

    result_uninstall = runner.invoke(cli.cli, ["uninstall"], input="y\nn\n")
    assert result_uninstall.exit_code == 0
    assert not prefix.exists()

    result_install = runner.invoke(cli.cli, ["install", "--dry-run"])
    assert result_install.exit_code == 0
    assert prefix.exists()
