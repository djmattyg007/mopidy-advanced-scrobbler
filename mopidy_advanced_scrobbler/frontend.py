from __future__ import annotations

import logging
import sqlite3
import time
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import pykka
import pylast

from mopidy.core import CoreListener


from mopidy_advanced_scrobbler import Extension, schema
from mopidy_advanced_scrobbler.models import Correction, prepare_play


if TYPE_CHECKING:
    from typing import Optional, TypedDict
    from mopidy.models import TlTrack, Track


logger = logging.getLogger(__name__)


PYLAST_ERRORS = (
    pylast.MalformedResponseError,
    pylast.NetworkError,
    pylast.WSError,
)


class NowPlayingData(TypedDict):
    artist: str
    title: str
    album: Optional[str]
    mbid: Optional[str]
    duration: Optional[int]


def prepare_now_playing_data(track: Track, correction: Correction) -> NowPlayingData:
    if correction:
        artist = correction.artist
        title = correction.title
    else:
        artist = ", ".join(sorted([artist.name for artist in track.artists]))
        title = track.name or ""

    data = {
        "artist": artist,
        "title": title,
    }

    if correction:
        data["album"] = correction.album or ""
    elif track.album and track.album.name:
        data["album"] = track.album.name

    if track.length:
        data["duration"] = track.length // 1000

    if track.musicbrainz_id:
        data["mbid"] = track.musicbrainz_id

    return data


class DebounceActor(pykka.ThreadingActor):
    def __init__(self, debounce_id: str, wrapped: pykka.CallableProxy, timeout: int, *args, **kwargs):
        super().__init__()

        self.debounce_id = debounce_id
        self.timeout = timeout
        self.args = args
        self.kwargs = kwargs

        self._wrapped = wrapped
        self._proxy = self.actor_ref.proxy()

    def on_start(self):
        self._proxy.start_timer()
        logger.debug("Started debounce for ID %s", self.debounce_id)

    def start_timer(self):
        logger.debug("Started debounce timeout for ID %s", self.debounce_id)
        time.sleep(self.timeout)
        logger.debug("Finished debounce timeout for ID %s", self.debounce_id)
        self._proxy.finish_timer()

    def finish_timer(self):
        logger.debug("Successful debounce for ID %s", self.debounce_id)
        self._wrapped(*self.args, **self.kwargs)
        self.stop()


class AdvancedScrobblerFrontend(pykka.ThreadingActor, CoreListener):
    def __init__(self, config, core):
        super().__init__()
        self.config = config["advanced_scrobbler"]
        self.lastfm = None

        self._data_dir = Extension.get_data_dir(config)
        self._dbpath = self._data_dir / "advanced_scrobbler.db"
        self._connection = None

        self._proxy = self.actor_ref.proxy()
        self._now_playing_notify_debouncer = None

    def is_uri_allowed(self, uri: str) -> bool:
        parsed_uri = urlparse(uri)
        if not parsed_uri.scheme:
            return False
        elif parsed_uri.scheme in self.config["ignored_uri_schemes"]:
            return False

        return True

    def _connect(self):
        if not self._connection:
            logger.info("Connecting to Advanced-Scrobbler sqlite database at %s", self._dbpath)
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
        except Exception as e:
            logger.exception(f"Error during Advanced-Scrobbler database preparation: {e}")
            raise

        try:
            self.lastfm = pylast.LastFMNetwork(
                api_key=self.config["api_key"],
                api_secret=self.config["api_secret"],
                username=self.config["username"],
                password_hash=pylast.md5(self.config["password"]),
            )
            logger.info("Advanced-Scrobbler connected to Last.fm")
        except PYLAST_ERRORS as e:
            logger.exception(f"Error during Advanced-Scrobbler Last.fm setup: {e}")
            raise

    def on_stop(self):
        if self._now_playing_notify_debouncer:
            self._now_playing_notify_debouncer.actor_ref.stop(block=True)

    def track_playback_started(self, tl_track: TlTrack):
        track = tl_track.track
        if not self.is_uri_allowed(track.uri):
            return

        logger.debug("Advanced-Scrobbler track playback started: %s", track.uri)

        if self._now_playing_notify_debouncer:
            self._now_playing_notify_debouncer.actor_ref.stop(block=False)

        self._now_playing_notify_debouncer = DebounceActor.start(track.uri, self._proxy.debounced_now_playing_notify, 5, track).proxy()

    def track_playback_ended(self, tl_track: TlTrack, time_position):
        track = tl_track.track
        if not self.is_uri_allowed(track.uri):
            return

        time_position_sec = time_position / 1000
        logger.debug("Advanced-Scrobbler track playback ended after %s: %s", int(time_position_sec), track.uri)

        try:
            correction = schema.find_correction(self._connect(), track.uri)
        except Exception as e:
            logger.exception(f"Error while finding scrobbler correction for track with URI '{track.uri}': {e}")
            correction = None

        play = prepare_play(track, correction, int(time.time() - time_position_sec))
        if play.duration < 30:
            logger.debug("Advanced-Scrobbler track to short to scrobble (%d secs): %s", time_position_sec, track.uri)
            return

        threshold = self.config["scrobble_time_threshold"] / 100
        threshold_duration = play.duration * threshold
        if time_position_sec < threshold_duration and time_position_sec < 240:
            logger.debug(
                "Advanced-Scrobbler track not played long enough to scrobble (%d/%d secs): %s",
                time_position_sec, play.duration, track.uri,
            )
            return

        try:
            schema.record_play(self._connect(), play)
        except Exception as e:
            logger.exception(f"Error while recording play for track with URI '{track.uri}: {e}")
            raise

    def debounced_now_playing_notify(self, track: Track):
        self._now_playing_notify_debouncer = None
        logger.info("Advanced-Scrobbler submitting now playing notification: %s", track.uri)

        try:
            correction = schema.find_correction(self._connect(), track.uri)
        except Exception as e:
            logger.exception(f"Error while finding correction for track with URI '{track.uri}': {e}")
            correction = None

        now_playing_data = prepare_now_playing_data(track, correction)

        try:
            self.lastfm.update_now_playing(**now_playing_data)
        except PYLAST_ERRORS as e:
            logger.exception(f"Error while submitting now playing data to Last.fm: {e}")
