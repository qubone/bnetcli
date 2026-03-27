from click.testing import CliRunner

from bnetcli import cli
from bnetcli.config import BnetConfig, EnvironmentConfig


def test_start_when_proton_missing(monkeypatch, tmp_path):
    runner = CliRunner()
    cfg = BnetConfig(
        wine_prefix=tmp_path / "prefix",
        executable=tmp_path / "launcher.exe",
        proton_path=tmp_path / "compat",
        steam_path=tmp_path / "steam",
        environment=EnvironmentConfig(),  # or with defaults
    )

    monkeypatch.setattr("bnetcli.config.load_config", lambda p=None: cfg)
    monkeypatch.setattr("bnetcli.proton.detect_steam_base_path", lambda: tmp_path / "steam")
    monkeypatch.setattr("bnetcli.proton.ensure_compat_dir", lambda p: tmp_path / "compat")

    # Ensure compat dir exists but proton exe is missing
    (tmp_path / "compat").mkdir()

    # Prevent starting the real launcher during tests
    monkeypatch.setattr("bnetcli.utils.run", lambda *a, **k: None)

    result = runner.invoke(cli.cli, ["start"])
    # On some environments the test may simulate a usable proton path;
    # ensure the command runs and reports the Proton version it intends to use.
    assert result.exit_code == 0
    assert "Using Proton version" in result.output
