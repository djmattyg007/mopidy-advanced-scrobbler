import logging
import pykka
import pylast
from typing import Optional, TypedDict

from ._service import Service


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

    def send_now_playing_notification(self, now_playing_data: NowPlayingData):
        try:
            self._network.update_now_playing(**now_playing_data)
        except PYLAST_ERRORS as exc:
            logger.exception(f"Error while submitting now playing data to {self._network}: {exc}")


network_service = Service(AdvancedScrobblerNetwork)
