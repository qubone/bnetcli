from pathlib import Path

import pytest
from click.testing import CliRunner

from bnetcli import cli
from bnetcli.config import BnetConfig, EnvironmentConfig


def test_install_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    runner: CliRunner = CliRunner()

    # Stub out system checks and other side effects
    monkeypatch.setattr("bnetcli.system.print_system_summary", lambda: None)
    monkeypatch.setattr("bnetcli.config.load_config", lambda path=None:
        BnetConfig(
        proton_path=None,
        wine_prefix=Path("/tmp/prefix"),
        installer_path=Path("/tmp/installer.exe"),
        environment=EnvironmentConfig()
    ))
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
    monkeypatch.setattr("bnetcli.config.load_config", lambda path=None: BnetConfig(wine_prefix=d))

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

    cfg = BnetConfig(
        wine_prefix=prefix,
        installer_path=installer_path,
        proton_path=proton_dir,
        environment=EnvironmentConfig(),
    )
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
    cfg = BnetConfig(
        wine_prefix=prefix,
        installer_path=installer_path,
        proton_path=proton_dir,
        environment=EnvironmentConfig(),
    )

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


def test_list_games_detects_installed_games(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = CliRunner()
    prefix = tmp_path / "bnet_prefix"
    (prefix / "drive_c" / "Program Files (x86)" / "World of Warcraft").mkdir(parents=True)
    (prefix / "drive_c" / "Program Files (x86)" / "Diablo IV").mkdir(parents=True)

    cfg = BnetConfig(
        wine_prefix=prefix,
        executable=prefix / "drive_c" / "Program Files (x86)" / "Battle.net" / "Battle.net Launcher.exe",
        proton_path=tmp_path / "compat",
        environment=EnvironmentConfig(),
    )
    monkeypatch.setattr("bnetcli.config.load_config", lambda p=None: cfg)

    result = runner.invoke(cli.cli, ["list-games"])
    assert result.exit_code == 0
    assert "World of Warcraft" in result.output
    assert "Diablo IV" in result.output


def test_game_info_pretty_bytes_and_str(tmp_path: Path) -> None:
    game_dir = tmp_path / "World of Warcraft"
    game_dir.mkdir(parents=True)
    # Create some files with known sizes
    (game_dir / "a.bin").write_bytes(b"x" * 1536)
    (game_dir / "b.bin").write_bytes(b"x" * 2048)

    info = cli.GameInfo.from_detected_path("World of Warcraft", game_dir)
    assert info.name == "World of Warcraft"
    assert info.path == game_dir
    assert info.file_count == 2
    assert info.disk_usage_bytes == 3584
    assert info.pretty_bytes().endswith("KB")
    assert "World of Warcraft" in str(info)
    assert "files" in str(info)


def test_find_installed_blizzard_games_returns_game_info(tmp_path: Path) -> None:
    prefix = tmp_path / "bnet_prefix"
    game_path = prefix / "drive_c" / "Program Files (x86)" / "Diablo IV"
    game_path.mkdir(parents=True)
    (game_path / "game.exe").write_bytes(b"x")

    found = cli.find_installed_blizzard_games(prefix)
    assert "Diablo IV" in found
    info = found["Diablo IV"]
    assert isinstance(info, cli.GameInfo)
    assert info.name == "Diablo IV"
    assert info.path == game_path
    assert info.file_count == 1

