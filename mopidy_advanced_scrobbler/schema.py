import logging
import pathlib
import sqlite3
from typing import Optional

from mopidy_advanced_scrobbler.models import Correction, Play


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


def find_correction(conn: Connection, track_uri: str) -> Optional[Correction]:
    query = "SELECT * FROM corrections WHERE track_uri = ?"
    logger.debug("Executing DB query: %s", query)
    cursor = conn.execute(query, (track_uri,))
    result = cursor.fetchone()
    if result:
        return Correction(**result)
    else:
        return None


def record_play(conn: Connection, play: Play):
    query = """
        INSERT INTO plays (
            track_uri, artist, title, album, corrected, musicbrainz_id, duration, played_at
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?
        )
    """
    logger.debug("Executing DB query: %s", query)
    args = (
        play.track_uri,
        play.artist,
        play.title,
        play.album,
        play.corrected.value,
        play.musicbrainz_id,
        play.duration,
        play.played_at,
    )
    with conn:
        conn.execute(query, args)
