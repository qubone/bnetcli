# bnetcli
Standalone battle.net launcher for Linux-based systems.

## Getting Started

1. Create and activate a Python virtual environment.
2. Install dependencies with `pip install -e .`.
3. Run `bnetcli install` to install Battle.net.
4. Run `bnetcli start` to launch Battle.net.

## Available Commands

### `bnetcli install`
Install Battle.net using Proton (GE Proton by default).

Options:
- `--proton-version`, `-p`: Proton version (default: `auto`)
- `--dry-run`: Show what would be done without running installer
- `--config-file`: Path to custom config file

Behavior:
1. Loads config values.
2. Ensures Proton compatibility directory exists.
3. Detects or installs Proton.
4. Creates Wine prefix.
5. Downloads installer and launches it (unless `--dry-run`).

### `bnetcli start`
Launch Battle.net from your configured prefix.

Options:
- `--disable-browser/--enable-browser` (default: `--disable-browser`)
- `--start-minimized/--normal` (default: `--normal`)
- `--proton-version` (default: `GE-Proton10-24`)
- `--config-file`: Path to custom config file

Behavior:
1. Loads config values.
2. Detects Steam path and Proton compatibility tools.
3. Builds environment variables and runs Proton.

### `bnetcli repair-prefix`
Repair your Battle.net Wine prefix.

Options:
- `--config-file`: Path to custom config file

Behavior:
1. Loads config.
2. Runs prefix repair on `wine_prefix`.

### `bnetcli uninstall`
Uninstall Battle.net data and optionally proton tools.

Options:
- `--config-file`: Path to custom config file

Behavior:
1. Loads config.
2. Prompts to remove configured `wine_prefix`.
3. Removes installer file (if present).
4. Prompts to optionally remove all `GE-Proton*` directories in `proton_path`.

### `bnetcli doctor`
Run system diagnostics.

## Troubleshooting

### 1) Ensure paths are expanded and absolute
In config, `~` values are now supported, but the launcher expects valid paths. Example:

```yaml
wine_prefix: "~/Games/battlenet/pfx"
executable: "~/Games/battlenet/pfx/drive_c/Program Files (x86)/Battle.net/Battle.net Launcher.exe"
proton_path: "~/.local/share/Steam/compatibilitytools.d"
```

### 2) Install `protonup` for Proton auto-management
System checks require `protonup`. On Arch:

```bash
sudo pacman -S protonup
```

or with pip:

```bash
pip install protonup
```

Then run:

```bash
bnetcli install --dry-run
```

### 3) Common runtime failure
If Proton returns non-zero, verify:
- steam is installed and path exists
- configured `wine_prefix` contains valid Battle.net prefix
- Battle.net executable exists in the prefix path

### 4) Useful commands

```bash
bnetcli doctor
bnetcli install --dry-run
bnetcli install
bnetcli start
```

### Example uninstall

```bash
bnetcli uninstall
```

This will remove your configured Wine prefix and installer file. It prompts to optionally clean Proton directories.

### Games ###

World of Warcraft default installation path:
C:\Program Files (x86)\World of Warcraft