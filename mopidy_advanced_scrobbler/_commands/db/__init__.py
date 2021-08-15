from pathlib import Path

from mopidy_advanced_scrobbler._commands import AbortCommand
from mopidy_advanced_scrobbler._commands.output import stderr, stdout
from mopidy_advanced_scrobbler.db import SCHEMA_VERSION, Connection, get_db_path, sqlite3


def connect_internal_db(config) -> Connection:
    db_path = get_db_path(config)
    if not db_path.is_file():
        stderr.print("Internal database does not exist.", style="error")
        raise AbortCommand

    stdout.print("Connecting to internal database.", style="notice")
    db: Connection = sqlite3.connect(
        db_path,
        timeout=config["advanced_scrobbler"]["db_timeout"],
        factory=Connection,
    )

    internal_user_version = db.execute("PRAGMA user_version").fetchone()["user_version"]
    if internal_user_version != SCHEMA_VERSION:
        stderr.print(
            f"Internal database schema is out of date. Latest version is v{SCHEMA_VERSION}.",
            style="error",
        )
        raise AbortCommand

    stdout.print("Connected to internal database.", style="info")
    return db


def _connect_external_db(db_path: Path, config) -> Connection:
    if not db_path.is_file():
        stderr.print("Specified external database file does not exist.", style="error")
        raise AbortCommand

    stdout.print("Connecting to external database.", style="notice")
    db: Connection = sqlite3.connect(
        db_path,
        timeout=config["advanced_scrobbler"]["db_timeout"],
        factory=Connection,
    )

    external_user_version = db.execute("PRAGMA user_version").fetchone()["user_version"]
    if external_user_version != SCHEMA_VERSION:
        stderr.print(
            f"External database schema is out of date. Latest version is v{SCHEMA_VERSION}.",
            style="error",
        )
        db.close()
        raise AbortCommand

    return db


def connect_external_db(db_path: Path, config) -> Connection:
    db = _connect_external_db(db_path, config)
    stdout.print("Connected to external database.", style="info")
    return db


def verify_external_db(db_path: Path, config):
    _connect_external_db(db_path, config)
    stdout.print("Verified external database.", style="info")


def attach_external_db(db: Connection, db_path: Path):
    db.execute("ATTACH DATABASE ? as ext", (str(db_path),))
    stdout.print("Connected to external database.", style="info")


__all__ = (
    "connect_internal_db",
    "connect_external_db",
    "verify_external_db",
    "attach_external_db",
)
