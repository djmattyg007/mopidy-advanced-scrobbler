from __future__ import annotations

from enum import Enum
import logging
from pathlib import Path
import pykka
import sqlite3
from time import time as _time
from typing import TYPE_CHECKING

from ._service import Service

if TYPE_CHECKING:
    from typing import Collection, List, Optional


from mopidy_advanced_scrobbler import Extension
from mopidy_advanced_scrobbler.models import Corrected, Correction, Play, RecordedPlay, PlayEdit


logger = logging.getLogger(__name__)


def time() -> int:
    return int(_time())


class DbClientError(Exception):
    pass


class SortDirectionEnum(Enum):
    SORT_ASC = "asc"
    SORT_DESC = "desc"


def dict_row_factory(cursor: sqlite3.Cursor, row: tuple):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class Connection(sqlite3.Connection):
    def __init__(self, *args, **kwargs):
        kwargs["isolation_level"] = None
        super().__init__(*args, **kwargs)
        self.row_factory = dict_row_factory
        self.execute("PRAGMA journal_mode = wal")
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

        user_version = conn.execute("PRAGMA user_version").fetchone()["user_version"]
        while user_version != schema_version:
            if user_version:
                logger.info("Upgrading Advanced-Scrobbler SQLite database schema v%s", user_version)
                filename = f"upgrade-v{user_version}.sql"
            else:
                logger.info("Creating Advanced-Scrobbler SQLite database schema v%s", schema_version)
                filename = "schema.sql"

            with open(self._sqlpath / filename) as fh:
                conn.executescript(fh.read())

            new_version = conn.execute("PRAGMA user_version").fetchone()["user_version"]
            assert new_version != user_version
            user_version = new_version
            logger.info("Successfully upgraded Advanced-Scrobbler SQLite database schema to v%s", user_version)

    def find_play(self, play_id: int) -> Optional[RecordedPlay]:
        conn = self._connect()

        query = "SELECT * FROM plays WHERE play_id = ?"
        logger.debug("Executing DB query: %s", query)
        cursor = conn.execute(query, (play_id,))
        result = cursor.fetchone()

        if result:
            return RecordedPlay.from_dict(result)
        else:
            return None

    def load_plays(
        self,
        *,
        sort_direction: SortDirectionEnum = SortDirectionEnum.SORT_DESC,
        page_num: int = 1,
        page_size: int = 50,
    ) -> Collection[RecordedPlay]:
        conn = self._connect()

        order = sort_direction.value
        limit = int(page_size)
        offset = (int(page_num) - 1) * limit

        query = f"SELECT * FROM plays ORDER BY play_id {order} LIMIT {limit} OFFSET {offset}"
        logger.debug("Executing DB query: %s", query)
        cursor = conn.execute(query)

        plays: List[RecordedPlay] = []
        for row in cursor:
            plays.append(RecordedPlay.from_dict(row))

        return tuple(plays)

    def get_plays_count(self, *, only_unsubmitted: bool = False) -> int:
        conn = self._connect()

        query = "SELECT COUNT(*) as plays_count FROM plays"
        if only_unsubmitted:
            query += " WHERE submitted_at IS NULL"

        logger.debug("Executing DB query: %s", query)
        cursor = conn.execute(query)
        result = cursor.fetchone()

        return int(result["plays_count"])

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

    def edit_play(self, play_edit: PlayEdit):
        conn = self._connect()

        play = self.find_play(play_edit.play_id)
        if not isinstance(play, RecordedPlay):
            raise DbClientError(f"No play found with ID '{play_edit.play_id}'.")
        elif play_edit.track_uri != play.track_uri:
            raise DbClientError(f"Mismatched track URI for play with ID '{play_edit.play_id}'.")
        elif play.submitted_at:
            raise DbClientError(f"The relevant play was already submitted and can no longer be updated.")

        with conn:
            conn.execute("BEGIN")

            play_update_args = (play_edit.artist, play_edit.title, play_edit.album, Corrected.MANUALLY_CORRECTED)
            if play_edit.update_all_unsubmitted:
                play_update_query = """
                UPDATE plays SET artist = ?, title = ?, album = ?, corrected = ?
                WHERE track_uri = ? AND submitted_at IS NULL
                """
                play_update_args += (play.track_uri,)
            else:
                play_update_query = "UPDATE plays SET artist = ?, title = ?, album = ?, corrected = ? WHERE play_id = ?"
                play_update_args += (play.play_id,)

            logger.debug("Executing DB query: %s", play_update_query)
            conn.execute(play_update_query, play_update_args)

            if play_edit.save_correction:
                correction_upsert_query = """
                INSERT INTO corrections (track_uri, artist, title, album) VALUES (?, ?, ?, ?)
                ON CONFLICT (track_uri) DO
                UPDATE SET artist = excluded.artist, title = excluded.title, album = excluded.album
                """
                logger.debug("Executing DB query: %s", correction_upsert_query)
                conn.execute(
                    correction_upsert_query,
                    (play.track_uri, play_edit.artist, play_edit.title, play_edit.album),
                )

    def delete_play(self, play_id: int) -> bool:
        play = self.find_play(play_id)
        if play.submitted_at:
            raise DbClientError("The relevant play was already submitted and can only be deleted through cleaning.")

        delete_query = "DELETE FROM plays WHERE play_id = ? AND submitted_at IS NULL"
        delete_args = (play_id,)

        with self._connect() as conn:
            logger.debug("Executing DB query: %s", delete_query)
            cursor = conn.execute(delete_query, delete_args)
            return cursor.rowcount == 1

    def mark_play_submitted(self, play_id: int) -> bool:
        play = self.find_play(play_id)
        if play.submitted_at:
            raise DbClientError("The relevant play was already submitted.")

        update_query = "UPDATE plays SET submitted_at = ? WHERE play_id = ? AND submitted_at IS NULL"
        update_args = (time(), play_id)

        with self._connect() as conn:
            logger.debug("Executing DB query: %s", update_query)
            cursor = conn.execute(update_query, update_args)
            return cursor.rowcount == 1

    def find_correction(self, track_uri: str) -> Optional[Correction]:
        conn = self._connect()

        query = "SELECT * FROM corrections WHERE track_uri = ?"
        logger.debug("Executing DB query: %s", query)
        cursor = conn.execute(query, (track_uri,))
        result = cursor.fetchone()

        if result:
            return Correction.from_dict(result)
        else:
            return None

    def load_corrections(self, *, page_num: int = 1, page_size: int = 50) -> Collection[Correction]:
        conn = self._connect()

        limit = int(page_size)
        offset = (int(page_num) - 1) * limit

        query = f"SELECT * FROM corrections LIMIT {limit} OFFSET {offset}"
        logger.debug("Executing DB query: %s", query)
        cursor = conn.execute(query)

        corrections: List[Correction] = []
        for row in cursor:
            corrections.append(Correction.from_dict(row))

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
