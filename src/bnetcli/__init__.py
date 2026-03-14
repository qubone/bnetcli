"""bnetcli - A Battle.net launcher for Linux using Proton/Wine."""

from typing import NoReturn


def main() -> None:
    """Print a greeting used by tests and CLI smoke checks."""
    print("Hello from bnetcli!")  # noqa: T201


def _exit_with_code(code: int) -> NoReturn:
    raise SystemExit(code)
