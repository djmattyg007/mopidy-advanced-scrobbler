import json
import logging
import sqlite3

import pykka
import pylast

from mopidy.core import CoreListener

from mopidy_advanced_scrobbler import Extension, schema


logger = logging.getLogger(__name__)


PYLAST_ERRORS = (
    pylast.NetworkError,
    pylast.MalformedResponseError,
    pylast.WSError,
)


class RecorderFrontend(pykka.ThreadingActor, CoreListener):
    def __init__(self, config, core):
        super().__init__()
        self.config = config["advanced_scrobbler"]
        self.lastfm = None
        self.last_start_time = None

        self._data_dir = Extension.get_data_dir(config)
        self._dbpath = self._data_dir / "advanced_scrobbler.db"
        self._connection = None

    def _connect(self):
        if not self._connection:
            logger.debug("Connecting to sqlite database at %s", self._dbpath)
            self._connection = sqlite3.connect(
                self._dbpath,
                timeout=self.config["db_timeout"],
                check_same_thread=False,
                factory=schema.Connection,
            )
        return self._connection

    def on_start(self):
        try:
            with self._connect() as connection:
                schema.prepare(connection)
        except Exception as exc:
            logger.error(f"Error during Advanced-Scrobbler database preparation: {exc}")
            self.stop()
            return

        try:
            self.lastfm = pylast.LastFMNetwork(
                api_key=self.config["api_key"],
                api_secret=self.config["api_secret"],
                username=self.config["username"],
                password_hash=pylast.md5(self.config["password"]),
            )
            logger.info("Advanced-Scrobbler connected to Last.fm")
        except PYLAST_ERRORS as exc:
            logger.error(f"Error during Advanced-Scrobbler Last.fm setup: {exc}")
            self.stop()

    def track_playback_started(self, tl_track):
        logger.debug("Track playback started: %s", json.dumps(tl_track.track.serialize(), indent=4))

    def track_playback_ended(self, tl_track, time_position):
        logger.debug("Track playback ended after %s: %s", time_position, json.dumps(tl_track.track.serialize(), indent=4))
