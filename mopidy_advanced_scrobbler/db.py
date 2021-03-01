from __future__ import annotations

import logging
from pathlib import Path
import pykka
import sqlite3
from typing import TYPE_CHECKING

from ._service import Service

if TYPE_CHECKING:
    from typing import Collection, Optional


from mopidy_advanced_scrobbler import Extension
from mopidy_advanced_scrobbler.models import Correction, Play


logger = logging.getLogger(__name__)


class Connection(sqlite3.Connection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.execute("PRAGMA foreign_keys = ON")


class AdvancedScrobblerDb(pykka.ThreadingActor):
    schema_version = 1

    def __init__(self, config):
        super().__init__()

        self._dbpath = Extension.get_data_dir(config) / "advanced_scrobbler.db"
        self._timeout = config["advanced_scrobbler"]["db_timeout"]

        self._sqlpath = Path(__file__).parent / "sql"

        self._connection: Optional[Connection] = None

    def _connect(self):
        if not self._connection:
            logger.info("Connecting to Advanced-Scrobbler sqlite database at %s", self._dbpath)
            self._connection = sqlite3.connect(
                self._dbpath,
                timeout=self._timeout,
                factory=Connection,
            )
            logger.debug("Connected to Advanced-Scrobbler sqlite database at %s", self._dbpath)
        return self._connection

    def on_start(self):
        try:
            self.prepare_db()
        except Exception as exc:
            logger.exception(f"Error during Advanced-Scrobbler database preparation: {exc}")
            raise

    def on_stop(self):
        if self._connection:
            self._connection.close()

    def prepare_db(self):
        conn = self._connect()
        schema_version = AdvancedScrobblerDb.schema_version

        user_version = conn.execute("PRAGMA user_version").fetchone()[0]
        while user_version != schema_version:
            if user_version:
                logger.info("Upgrading Advanced-Scrobbler SQLite database schema v%s", user_version)
                filename = f"upgrade-v{user_version}.sql"
            else:
                logger.info("Creating Advanced-Scrobbler SQLite database schema v%s", schema_version)
                filename = "schema.sql"

            with open(self._sqlpath / filename) as fh:
                conn.executescript(fh.read())

            new_version = conn.execute("PRAGMA user_version").fetchone()[0]
            assert new_version != user_version
            user_version = new_version
            logger.info("Successfully upgraded Advanced-Scrobbler SQLite database schema to v%s", user_version)

    def find_play(self, track_uri: str) -> Optional[Play]:
        conn = self._connect()

        query = "SELECT * FROM plays WHERE track_uri = ?"
        logger.debug("Executing DB query: %s", query)
        cursor = conn.execute(query, (track_uri,))
        result = cursor.fetchone()

        if result:
            return Play(**result)
        else:
            return None

    def load_plays(self, page_num: int = 1, page_size: int = 50) -> Collection[Play]:
        conn = self._connect()

        limit = int(page_size)
        offset = (int(page_num) - 1) * limit
        query = f"SELECT * FROM plays LIMIT {limit} OFFSET {offset}"
        logger.debug("Executing DB query: %s", query)
        cursor = conn.execute(query)

        plays = []
        for row in cursor:
            plays.append(Play(**row))

        return tuple(plays)

    def record_play(self, play: Play):
        query = """
            INSERT INTO plays (
                track_uri, artist, title, album, corrected, musicbrainz_id, duration, played_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?
            )
        """
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

        with self._connect() as conn:
            logger.debug("Executing DB query: %s", query)
            conn.execute(query, args)

    def find_correction(self, track_uri: str) -> Optional[Correction]:
        conn = self._connect()

        query = "SELECT * FROM corrections WHERE track_uri = ?"
        logger.debug("Executing DB query: %s", query)
        cursor = conn.execute(query, (track_uri,))
        result = cursor.fetchone()

        if result:
            return Correction(**result)
        else:
            return None

    def load_corrections(self, page_num: int = 1, page_size: int = 50) -> Collection[Correction]:
        conn = self._connect()

        limit = int(page_size)
        offset = (int(page_num) - 1) * limit
        query = f"SELECT * FROM corrections LIMIT {limit} OFFSET {offset}"
        logger.debug("Executing DB query: %s", query)
        cursor = conn.execute(query)

        corrections = []
        for row in cursor:
            corrections.append(Correction(**row))

        return tuple(corrections)

    def record_correction(self, correction: Correction):
        query = """
            INSERT OR REPLACE INTO corrections (
                track_uri, artist, title, album
            ) VALUES (
                ?, ?, ?, ?
            )
        """
        args = (
            correction.track_uri,
            correction.artist,
            correction.title,
            correction.album,
        )

        with self._connect() as conn:
            logger.debug("Executing DB query: %s", query)
            conn.execute(query, args)


db_service = Service(AdvancedScrobblerDb)
