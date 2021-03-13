import logging
import pykka
import pylast
from typing import Optional, TypedDict

from mopidy_advanced_scrobbler.models import Play
from ._service import Service


logger = logging.getLogger(__name__)


PYLAST_ERRORS = (
    pylast.MalformedResponseError,
    pylast.NetworkError,
    pylast.WSError,
)


class NetworkException(Exception):
    pass


class NowPlayingData(TypedDict):
    artist: str
    title: str
    album: Optional[str]
    mbid: Optional[str]
    duration: Optional[int]


def format_now_playing_data(play: Play) -> NowPlayingData:
    data = {
        "artist": play.artist,
        "title": play.title,
    }

    if play.album:
        data["album"] = play.album,
    if play.duration:
        data["duration"] = play.duration
    if play.musicbrainz_id:
        data["mbid"] = play.musicbrainz_id

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
                password_hash=pylast.md5(self._config["password"])
            )
            logger.debug("Connected to Last.fm with username %s", self._config["username"])
        except PYLAST_ERRORS as exc:
            logger.exception(f"Error during Advanced-Scrobbler Last.fm setup: {exc}")
            raise

    def send_now_playing_notification(self, play: Play):
        now_playing_data = format_now_playing_data(play)

        try:
            self._network.update_now_playing(**now_playing_data)
        except PYLAST_ERRORS as exc:
            logger.exception(f"Error while sending now playing data to {self._network}: {exc}")
            raise NetworkException(f"Error while sending now playing data to {self._network}") from exc

    def submit_scrobble(self, play: Play):
        album = play.album if play.album else None
        mbid = play.musicbrainz_id if play.musicbrainz_id else None

        try:
            self._network.scrobble(
                artist=play.artist,
                title=play.title,
                album=album,
                timestamp=play.played_at,
                duration=play.duration,
                mbid=mbid,
            )
        except PYLAST_ERRORS as exc:
            logger.exception(f"Error while submitting scrobble to {self._network}: {exc}")
            raise NetworkException(f"Error while submitting scrobble to {self._network}") from exc


network_service = Service(AdvancedScrobblerNetwork)
