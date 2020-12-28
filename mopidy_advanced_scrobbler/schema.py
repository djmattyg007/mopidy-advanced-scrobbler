import logging
import pathlib
import sqlite3


logger = logging.getLogger(__name__)


schema_version = 1


class Connection(sqlite3.Connection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.execute("PRAGMA foreign_keys = ON")


def prepare(conn: Connection):
    sql_dir = pathlib.Path(__file__).parent / "sql"

    user_version = conn.execute("PRAGMA user_version").fetchone()[0]
    while user_version != schema_version:
        if user_version:
            logger.info("Upgrading Advanced-Scrobbler SQLite database schema v%s", user_version)
            filename = f"upgrade-v{user_version}.sql"
        else:
            logger.info("Creating Advanced-Scrobbler SQLite database schema v%s", schema_version)
            filename = "schema.sql"

        with open(sql_dir / filename) as fh:
            conn.executescript(fh.read())

        new_version = conn.execute("PRAGMA user_version").fetchone()[0]
        assert new_version != user_version
        user_version = new_version
