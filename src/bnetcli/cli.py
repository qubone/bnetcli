"""Command-line interface for bnetcli, a minimal Battle.net launcher using Proton."""
import logging
import os
from pathlib import Path

import click

from . import installer, proton, repair, system, utils, wine
from .config import load_config
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
    cfg = load_config(config_file)

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

    cfg = load_config(config_file)

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
            cfg["environment"],
        )
    else:
        click.secho(
            f"Would launch installer with: {proton_exe} run {installer_path} using prefix {prefix}",
            fg="cyan"
        )
        click.secho(f"Environment variables: {cfg['environment']}", fg="cyan")
    click.secho("Installation complete! You can run 'bnetcli start' to launch Battle.net.", fg="green", bold=True)

@cli.command()
@click.option("--proton-version", default="GE-Proton10-24", help="Proton version to use")
@click.option("--config-file", type=click.Path(exists=False), help="Optional path to config file")
def start(proton_version: str, config_file: Path | None):
    """Start the Battle.net launcher using the optionally specified Proton version."""
    cfg = load_config(config_file)

    prefix = Path(cfg["wine_prefix"])
    launcher_exe = Path(cfg["executable"])

    steam_path = detect_steam_base_path()
    if not steam_path:
        click.secho("Steam installation not detected. Please specify the path in the config file.", fg="red")

    compat_dir = ensure_compat_dir(steam_path)
    if not compat_dir.exists():
        raise click.ClickException("Proton compatibility tools directory not found")

    if not proton_version:
        latest_proton_version = detect_latest_proton(compat_dir)
        if not latest_proton_version:
            raise click.ClickException("No Proton version detected")

    click.echo(f"Using Proton version: {proton_version}")

    proton_exe = Path(cfg["proton_path"]) / proton_version / "proton"
    logger.debug("Looking for Proton executable at: %s", proton_exe)

    if not proton_exe.exists():
        raise click.ClickException("Proton executable not found")

    env = os.environ.copy()
    env.update(cfg["environment"])
    env["STEAM_COMPAT_DATA_PATH"] = str(prefix)
    env["STEAM_COMPAT_CLIENT_INSTALL_PATH"] = str(steam_path)

    click.echo(f"→ {proton_exe} run {launcher_exe}")

    utils.run(
        [str(proton_exe), "run", str(launcher_exe)],
        env=env,
    )


@cli.command()
def doctor():
    """Run system health diagnostics."""
    run_diagnostics()
