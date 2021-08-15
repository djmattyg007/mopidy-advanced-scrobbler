from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from mopidy import commands


if TYPE_CHECKING:
    from argparse import Namespace


def _pre_import_deps() -> None:
    """Pre-import dependencies to immediately highlight missing dependencies."""
    try:
        import readline  # noqa
    except ImportError:
        pass

    import prompt_toolkit  # noqa
    import questionary  # noqa
    import rich  # noqa


class AdvancedScrobblerCommand(commands.Command):
    def __init__(self):
        super().__init__()
        self.add_child("db", DbCommand())


class DbCommand(commands.Command):
    def __init__(self):
        super().__init__()
        self.add_child("sync-corrections", DbSyncCorrectionsCommand())


class DbSyncCorrectionsCommand(commands.Command):
    help = "Synchronise corrections with another Advanced Scrobbler database."

    def __init__(self):
        super().__init__()
        self.add_argument(
            "external_db",
            type=Path,
            help="Path to the external SQLite database file.",
        )
        self.add_argument(
            "--include-filesystem-uris",
            action="store_true",
            dest="include_filesystem_uris",
            default=False,
            help="By default, file: and local: URIs are skipped. Use this flag to not skip them.",
        )

    def run(self, args: Namespace, config):
        from ._commands import AbortCommand

        _pre_import_deps()

        from ._commands.db.sync_corrections import run

        try:
            exit_code = run(args, config)
        except AbortCommand:
            exit_code = 1

        if exit_code is None:
            exit_code = 0

        return exit_code
