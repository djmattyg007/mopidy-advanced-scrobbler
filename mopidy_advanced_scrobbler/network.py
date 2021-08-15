from __future__ import annotations

import logging
from typing import Iterable, Optional, TypedDict, cast

import pykka
import pylast

from mopidy_advanced_scrobbler.models import Play, RecordedPlay

from ._service import Service


logger = logging.getLogger(__name__)


class NetworkException(Exception):
    pass


class NowPlayingData(TypedDict):
    artist: str
    title: str
    album: Optional[str]
    mbid: Optional[str]
    duration: Optional[int]


class _PartialNowPlayingData(TypedDict, total=False):
    artist: str
    title: str
    album: Optional[str]
    mbid: Optional[str]
    duration: Optional[int]


class PlayData(NowPlayingData):
    timestamp: int


def format_now_playing_data(play: Play) -> NowPlayingData:
    data: _PartialNowPlayingData = {
        "artist": play.artist,
        "title": play.title,
    }

    if play.album:
        data["album"] = play.album
    else:
        data["album"] = None
    if play.duration:
        data["duration"] = play.duration
    else:
        data["duration"] = None
    if play.musicbrainz_id:
        data["mbid"] = play.musicbrainz_id
    else:
        data["mbid"] = None

    return cast(NowPlayingData, data)


def format_play_data(play: Play) -> PlayData:
    base_data = format_now_playing_data(play)

    data: PlayData = {
        **base_data,
        "timestamp": play.played_at,
    }

    return data


class AdvancedScrobblerNetwork(pykka.ThreadingActor):
    def __init__(self, config):
        super().__init__()
        self._config = config
        self._network = None

    def on_start(self):
        try:
            logger.info("Connecting to Last.fm with username %s", self._config["username"])
            self._network = pylast.LastFMNetwork(
                api_key=self._config["api_key"],
                api_secret=self._config["api_secret"],
                username=self._config["username"],
                password_hash=pylast.md5(self._config["password"]),
            )
            logger.debug("Connected to Last.fm with username %s", self._config["username"])
        except pylast.PyLastError as exc:
            logger.exception(f"Error during Advanced-Scrobbler Last.fm setup: {exc}")
            raise

    def send_now_playing_notification(self, play: Play):
        now_playing_data = format_now_playing_data(play)

        logger.info("Sending 'now playing' notification: %s", play.track_uri)
        try:
            self._network.update_now_playing(**now_playing_data)
        except pylast.PyLastError as exc:
            logger.exception(f"Error while sending now playing data to {self._network}: {exc}")
            raise NetworkException(
                f"Error while sending now playing data to {self._network}"
            ) from exc

    def submit_scrobble(self, play: RecordedPlay):
        play_data = format_play_data(play)

        logger.info("Submitting scrobble for play %d: %s", play.play_id, play.track_uri)
        try:
            self._network.scrobble(**play_data)
        except pylast.PyLastError as exc:
            logger.exception(f"Error while submitting scrobble to {self._network}: {exc}")
            raise NetworkException(f"Error while submitting scrobble to {self._network}") from exc

    def submit_scrobbles(self, plays: Iterable[RecordedPlay]):
        plays_data = []
        play_ids = []
        for play in plays:
            plays_data.append(format_play_data(play))
            play_ids.append(play.play_id)

        logger.info("Submitting scrobbles for plays: %s", ", ".join(map(str, play_ids)))
        try:
            self._network.scrobble_many(plays_data)
        except pylast.PyLastError as exc:
            logger.exception(f"Error while submitting scrobbles to {self._network}: {exc}")
            raise NetworkException(f"Error while submitting scrobbles to {self._network}") from exc


network_service = Service(AdvancedScrobblerNetwork)
