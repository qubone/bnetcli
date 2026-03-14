"""Command-line interface for bnetcli, a minimal Battle.net launcher using Proton."""
import logging
import os
from pathlib import Path

import click

from . import config, installer, proton, repair, system, utils, wine
from .doctor import run_diagnostics
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

    prefix = Path(cfg["wine_prefix"]).expanduser()
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
        Path(cfg["proton_path"]).expanduser()
        if cfg.get("proton_path")
        else None
    )

    proton_dir = proton.ensure_compat_dir(configured_path)

    version, proton_exe = proton.resolve_proton_version(
        proton_dir,
        proton_version
    )
    click.secho(f"Using Proton version: {version}", fg="cyan")
    prefix = Path(cfg["wine_prefix"]).expanduser()

    wine.create_prefix(prefix, proton_exe)

    installer_path = Path(cfg["installer_path"]).expanduser()
    if not dry_run:
        installer.download(installer_path)
    else:
        click.secho(f"Would download installer to: {installer_path}", fg="cyan")

    if not dry_run:
        installer.launch_installer(
            proton_exe,
            installer_path,
            prefix,
            cfg.get("environment", {}),
        )
    else:
        click.secho(
            f"Would launch installer with: {proton_exe} run {installer_path} using prefix {prefix}",
            fg="cyan"
        )
        click.secho(f"Environment variables: {cfg.get('environment', {})}", fg="cyan")
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
    prefix = Path(cfg["wine_prefix"]).expanduser()
    installer_path = (
        Path(cfg["installer_path"]).expanduser()
        if cfg.get("installer_path")
        else None
    )
    proton_path = (
        Path(cfg["proton_path"]).expanduser()
        if cfg.get("proton_path")
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


@cli.command()
@click.option("--disable-browser/--enable-browser", default=True, help="Disable Battle.net embedded browser.")
@click.option("--start-minimized/--normal", default=False, help="Start Battle.net minimized.")
@click.option("--proton-version", default="GE-Proton10-24", help="Proton version to use")
@click.option("--config-file", type=click.Path(exists=False), help="Optional path to config file")
def start(disable_browser: bool, start_minimized: bool, proton_version: str, config_file: Path | None):
    """Start the Battle.net launcher using the optionally specified Proton version."""
    cfg = config.load_config(config_file)

    prefix = Path(cfg["wine_prefix"])
    launcher_exe = Path(cfg["executable"])

    steam_path = detect_steam_base_path()
    if not steam_path:
        click.secho("Steam installation not detected. Please specify the path in the config file.", fg="red")

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

    proton_exe = Path(cfg["proton_path"]) / proton_version / "proton"
    logger.debug("Looking for Proton executable at: %s", proton_exe)

    if not proton_exe.exists():
        click.secho(
            f"Proton executable not found at: {proton_exe}. Continuing to attempt launch, but this may fail.",
            fg="yellow",
        )

    env = os.environ.copy()
    env.update(cfg.get("environment", {}))
    env["STEAM_COMPAT_DATA_PATH"] = str(prefix)
    env["STEAM_COMPAT_CLIENT_INSTALL_PATH"] = str(steam_path)

    click.echo(f"→ {proton_exe} run {launcher_exe}")



    cmd = [str(proton_exe), "run", str(launcher_exe)]
    if disable_browser:
        # These are ENV VARS for Proton/Wine
        env["PROTON_NO_ESYNC"] = "1"
        env["PROTON_NO_FSYNC"] = "1"
        # These are CLI FLAGS for the Battle.net EXE to stabilize the browser

        # Fix Agent went to sleep error
        env["WINE_SIMULATE_WRITECOPY"] = "1"

        cmd.extend(["--no-sandbox", "--disable-gpu"])
        click.secho("Applying browser stability fixes (esync/fsync off + no-sandbox)", fg="yellow")
    if start_minimized:
        # This MUST be a CLI flag, not an environment variable
        cmd.append("--autostarted")
        click.secho("Starting Battle.net with --autostarted flag", fg="yellow")



    try:
        utils.run(
            [str(proton_exe), "run", str(launcher_exe)],
            env=env,
        )
    except FileNotFoundError as exc:
        raise click.ClickException(f"Failed to launch Battle.net: {exc}") from exc


@cli.command()
def doctor():
    """Run system health diagnostics."""
    run_diagnostics()
