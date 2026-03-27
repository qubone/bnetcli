"""Command-line interface for bnetcli, a minimal Battle.net launcher using Proton."""
import logging
import os
from pathlib import Path

import click

from . import config, installer, proton, repair, system, utils, wine
from .doctor import run_diagnostics
from .game_info import GameInfo, find_installed_blizzard_games
from .paths import CONFIG_FILE_PATH
from .proton import detect_latest_proton, detect_steam_base_path, ensure_compat_dir

logger = logging.getLogger(__name__)

@click.group()
@click.option("-v", "--verbose", count=True, help="Increase verbosity (-v, -vv)")
def cli(verbose: int):
    """Minimal Battle.net launcher using Proton."""
    level = logging.WARNING

    if verbose == 1:
        level = logging.INFO
    elif verbose >= 2:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s"
    )

@cli.command()
@click.option("--config-file", type=click.Path(exists=False), help="Optional path to config file")
def repair_prefix(config_file: Path | None):
    """Repair Battle.net Wine prefix."""
    cfg = config.load_config(config_file)

    prefix = cfg.wine_prefix
    if prefix is None:
        click.secho("Wine prefix path is not configured. Please set 'wine_prefix' in your config file.", fg="red")
        return
    click.secho(f"Repairing Battle.net prefix at: {prefix}", fg="yellow")
    repair.repair_prefix(prefix)

@cli.command()
@click.option("--proton-version", "-p", default="auto",
              help="Proton version to use (default: auto-detect latest)")
@click.option("--dry-run", is_flag=True, help="Show what would be done without executing")
@click.option("--config-file", type=click.Path(exists=False), help="Optional path to config file")
def install(proton_version: str, dry_run: bool, config_file: Path | None):
    """Install Battle.net launcher using Proton-GE."""
    click.secho("Installing Battle.net launcher...", fg="green", bold=True)
    click.secho("Performing system checks...", fg="cyan")
    system.print_system_summary()

    cfg = config.load_config(config_file)

    configured_path = (
        cfg.proton_path
        if cfg.proton_path
        else None
    )

    proton_dir = proton.ensure_compat_dir(configured_path)

    version, proton_exe = proton.resolve_proton_version(
        proton_dir,
        proton_version
    )
    click.secho(f"Using Proton version: {version}", fg="cyan")
    prefix = cfg.wine_prefix

    if prefix is None:
        click.secho("Wine prefix path is not configured. Please set 'wine_prefix' in your config file.", fg="red")
        return

    wine.create_prefix(prefix, proton_exe)

    installer_path = cfg.installer_path
    if installer_path is None:
        click.secho("No installer path configured; using default.", fg="yellow")
        installer_path = config.battlenet_installer_path()
    if not dry_run:
        installer.download(installer_path)
    else:
        click.secho(f"Would download installer to: {installer_path}", fg="cyan")

    if not dry_run:
        env_vars = cfg.environment.model_dump()
        env_vars.setdefault("STEAM_COMPAT_DATA_PATH", str(prefix))
        if not cfg.steam_path:
            raise click.ClickException("steam_path is not configured")

        env_vars.setdefault(
            "STEAM_COMPAT_CLIENT_INSTALL_PATH",
            str(cfg.steam_path)
        )
        try:
            installer.launch_installer(
                proton_exe,
                installer_path,
                prefix,
                env_vars,
            )
        except RuntimeError as exc:
            raise click.ClickException(f"Environment validation failed during install: {exc}") from exc
    else:
        click.secho(
            f"Would launch installer with: {proton_exe} run {installer_path} using prefix {prefix}",
            fg="cyan"
        )
        click.secho(f"Environment variables: {cfg.environment.model_dump()}", fg="cyan")
    click.secho("Installation complete! You can run 'bnetcli start' to launch Battle.net.", fg="green", bold=True)


def _remove_optional_installer(installer_path: Path | None) -> None:
    """Delete Battle.net installer file if it exists."""
    if installer_path is None:
        return

    if installer_path.exists():
        try:
            installer_path.unlink()
            click.secho(f"Removed installer at {installer_path}", fg="green")
        except OSError as exc:
            logger.warning("Failed to remove installer %s: %s", installer_path, exc)


def _uninstall_proton_versions(proton_path: Path) -> list[Path]:
    """Remove installed Proton GE versions and return removed dirs."""
    removed = proton.remove_installed_versions(proton_path)
    if removed:
        for entry in removed:
            click.secho(f"Removed Proton directory: {entry}", fg="green")
    else:
        click.secho("No GE-Proton versions found to remove.", fg="yellow")
    return removed


@cli.command()
@click.option("--config-file", type=click.Path(exists=False), help="Optional path to config file")
def uninstall(config_file: Path | None):
    """Uninstall Battle.net installation and optionally Proton."""
    cfg = config.load_config(config_file)
    prefix = cfg.wine_prefix
    if prefix is None:
        click.secho("Wine prefix path is not configured. Please set 'wine_prefix' in your config file.", fg="red")
        return

    installer_path = (
        cfg.installer_path
        if cfg.installer_path
        else None
    )
    proton_path = (
        cfg.proton_path
        if cfg.proton_path
        else None
    )

    click.secho("Uninstalling Battle.net and resetting local data...", fg="yellow", bold=True)
    if not click.confirm(f"Remove Battle.net prefix at {prefix}?", default=True):
        click.secho("Battle.net uninstall aborted.", fg="yellow")
        return

    wine.remove_prefix(prefix)
    click.secho(f"Removed Battle.net prefix at: {prefix}", fg="green")

    _remove_optional_installer(installer_path)

    if proton_path is not None and click.confirm(
        f"Also uninstall GE-Proton versions in {proton_path}?",
        default=False,
    ):
        _uninstall_proton_versions(proton_path)

    click.secho(
        "Battle.net uninstall complete. You can run 'bnetcli install' to reinstall.",
        fg="green",
        bold=True,
    )


def _build_start_env(prefix: Path, steam_path: Path, cfg: config.BnetConfig) -> dict[str, str]:
    """Build environment variables for starting Battle.net with Proton."""
    env = os.environ.copy()
    env.update(cfg.environment)
    env["STEAM_COMPAT_DATA_PATH"] = str(prefix)
    env["STEAM_COMPAT_CLIENT_INSTALL_PATH"] = str(steam_path)
    env["WINEDEBUG"] = "-all"
    env["PROTON_NO_ESYNC"] = "1"
    env["PROTON_NO_FSYNC"] = "1"
    env["WINEPREFIX"] = str(prefix)
    return env


def _get_proton_exe_path(cfg: config.BnetConfig, proton_version: str) -> Path:
    """Get the path to the Proton executable based on config and version."""
    if cfg.proton_path is None:
        click.secho("No Proton path configured; using default detection.", fg="yellow")
        compat_dir = ensure_compat_dir(None)
        return compat_dir / proton_version / "proton"
    return cfg.proton_path / proton_version / "proton"

def _get_wine_prefix(cfg: config.BnetConfig) -> Path:
    """Get the Wine prefix path from config, or raise an error if not set."""
    if cfg.wine_prefix is None:
        raise click.ClickException("Wine prefix path is not configured. Please set 'wine_prefix' in your config file.")
    return cfg.wine_prefix

def _ensure_required_env(env: dict[str, str]) -> None:
    """Ensure required environment variables for Proton are set."""
    required_env = ["WINEPREFIX", "STEAM_COMPAT_DATA_PATH", "STEAM_COMPAT_CLIENT_INSTALL_PATH"]
    missing_env = [k for k in required_env if not env.get(k)]
    if missing_env:
        raise click.ClickException(
            f"Missing required environment for Proton: {', '.join(missing_env)}"
        )


@cli.command()
@click.option("--disable-browser/--enable-browser", default=True, help="Disable Battle.net embedded browser.")
@click.option("--start-minimized/--normal", default=False, help="Start Battle.net minimized.")
@click.option("--proton-version", default="GE-Proton10-32", help="Proton version to use")
@click.option("--config-file", type=click.Path(exists=False),
               default=CONFIG_FILE_PATH, help="Optional path to config file")
def start(disable_browser: bool, start_minimized: bool, proton_version: str, config_file: Path | None):
    """Start the Battle.net launcher using the optionally specified Proton version."""
    cfg = config.load_config(config_file)

    prefix = _get_wine_prefix(cfg)
    launcher_exe = cfg.executable

    steam_path = detect_steam_base_path() or Path(cfg.steam_path or "~/.local/share/Steam").expanduser()
    if not steam_path.exists():
        click.secho("Steam installation not detected; using default location for compatibility tools.", fg="yellow")

    compat_dir = ensure_compat_dir(steam_path)
    if not compat_dir.exists():
        raise click.ClickException("Proton compatibility tools directory not found")

    if proton_version == "auto":
        detected_proton_version = detect_latest_proton(compat_dir)
        if detected_proton_version:
            proton_version = detected_proton_version
        else:
            click.secho("No Proton version detected; using default configured version.", fg="yellow")

    click.echo(f"Using Proton version: {proton_version}")

    proton_exe = _get_proton_exe_path(cfg, proton_version)
    logger.debug("Looking for Proton executable at: %s", proton_exe)
    if not proton_exe.exists():
        click.secho(
            f"Proton executable not found at: {proton_exe}. Continuing to attempt launch, but this may fail.",
            fg="yellow",
        )

    env = _build_start_env(prefix, steam_path, cfg)
    _ensure_required_env(env)

    if not prefix.exists():
        click.secho(f"Wine prefix does not exist: {prefix}. Proton may create it when launching.", fg="yellow")

    click.echo(f"→ {proton_exe} run {launcher_exe}")

    cmd = [str(proton_exe), "run", str(launcher_exe)]
    if disable_browser:
        env["PROTON_NO_ESYNC"] = "1"
        env["PROTON_NO_FSYNC"] = "1"
        env["WINE_SIMULATE_WRITECOPY"] = "1"
        cmd.extend(["--no-sandbox", "--disable-gpu"])
        click.secho("Applying browser stability fixes (esync/fsync off + no-sandbox)", fg="yellow")
    if start_minimized:
        cmd.append("--autostarted")
        click.secho("Starting Battle.net with --autostarted flag", fg="yellow")

    try:
        utils.run(cmd, env=env)
    except FileNotFoundError as exc:
        raise click.ClickException(f"Failed to launch Battle.net: {exc}") from exc


@cli.command()
@click.option("--config-file", type=click.Path(exists=False), help="Optional path to config file")
def list_games(config_file: Path | None):
    """List Blizzard games installed in the configured Wine prefix drive_c."""
    cfg = config.load_config(config_file)
    prefix = cfg.wine_prefix
    if prefix is None:
        click.secho("Wine prefix path is not configured. Please set 'wine_prefix' in your config file.", fg="red")
        return

    games: dict[str, GameInfo] = find_installed_blizzard_games(prefix)
    if not games:
        click.secho("No Blizzard games found in prefix drive_c. \
        Ensure games are installed in your Battle.net prefix.", fg="yellow")
        return

    click.secho("Installed Blizzard games:", fg="green")
    for game_info in sorted(games.values(), key=lambda g: g.name):
        click.echo(f"- {game_info}")

@cli.command()
@click.option("--config-file", type=click.Path(), help="Optional path")
@click.option("--auto-configure", "--ac", is_flag=True)
def configure(config_file: Path | None, auto_configure: bool):
    """Create or update configuration file with detected paths."""
    path = Path(config_file) if config_file else config.CONFIG_FILE_PATH

    if auto_configure:
        click.secho("Running auto configuration...", fg="cyan")

        cfg = config.generate_auto_config()
        config.save_config(cfg, path)

        click.secho(f"Config written to {path}", fg="green")
        return

    if not path.exists():
        cfg = config.BnetConfig()
        config.save_config(cfg, path)
        click.secho(f"Default config created at {path}", fg="green")
    else:
        click.secho(f"Config already exists at {path}", fg="yellow")


@cli.command()
def doctor():
    """Run system health diagnostics."""
    run_diagnostics()
