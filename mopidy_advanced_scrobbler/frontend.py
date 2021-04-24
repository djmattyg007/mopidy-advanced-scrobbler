from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Optional
from urllib.parse import urlparse

import pykka
from mopidy.core import CoreListener

from mopidy_advanced_scrobbler import Extension
from mopidy_advanced_scrobbler.db import db_service
from mopidy_advanced_scrobbler.models import Correction, prepare_play
from mopidy_advanced_scrobbler.network import NetworkException, network_service

from ._service import ActorRetrievalFailure


if TYPE_CHECKING:
    from mopidy.models import TlTrack, Track


logger = logging.getLogger(__name__)


class DebounceActor(pykka.ThreadingActor):
    def __init__(
        self,
        debounce_id: str,
        wrapped: pykka.CallableProxy,
        timeout: int,
        *args,
        **kwargs,
    ):
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
        self._wrapped.defer(*self.args, **self.kwargs)
        self.stop()


class AdvancedScrobblerFrontend(pykka.ThreadingActor, CoreListener):
    def __init__(self, config, core):
        super().__init__()
        self.config = config["advanced_scrobbler"]
        self._global_config = config

        self._data_dir = Extension.get_data_dir(config)

        self._proxy = self.actor_ref.proxy()
        self._now_playing_notify_debouncer = None

    def is_uri_allowed(self, uri: str) -> bool:
        parsed_uri = urlparse(uri)
        if not parsed_uri.scheme:
            return False
        elif parsed_uri.scheme in self.config["ignored_uri_schemes"]:
            return False

        return True

    def on_start(self):
        db_service.start_service(self._global_config)

        network_service.start_service(self.config)

    def on_stop(self):
        if self._now_playing_notify_debouncer:
            debouncer_stop_future = self._now_playing_notify_debouncer.actor_ref.stop(block=False)
        else:
            debouncer_stop_future = None

        network_service.stop_service()
        db_service.stop_service()
        if debouncer_stop_future:
            debouncer_stop_future.get()

    def track_playback_started(self, tl_track: TlTrack):
        track = tl_track.track
        if not self.is_uri_allowed(track.uri):
            return

        logger.debug("Advanced-Scrobbler track playback started: %s", track.uri)

        if self._now_playing_notify_debouncer:
            self._now_playing_notify_debouncer.actor_ref.stop(block=False)

        # Debounce for 5 seconds
        self._now_playing_notify_debouncer = DebounceActor.start(
            track.uri,
            self._proxy.debounced_now_playing_notify,
            5,
            track,
        ).proxy()

    def debounced_now_playing_notify(self, track: Track):
        self._now_playing_notify_debouncer = None
        logger.debug("Advanced-Scrobbler submitting now playing notification: %s", track.uri)

        correction: Optional[Correction]

        try:
            db = db_service.retrieve_service().get(timeout=10)
            correction = db.find_correction(track.uri).get(timeout=10)
        except ActorRetrievalFailure as exc:
            logger.exception(f"Database connection found to be unavailable: {exc}")
            correction = None
            db_service.request_service_restart(self._global_config)
        except Exception as exc:
            logger.exception(
                f"Error while finding scrobbler correction for track with URI '{track.uri}': {exc}"
            )
            correction = None

        play = prepare_play(track, -1, correction)

        try:
            network = network_service.retrieve_service().get(timeout=10)
            network.send_now_playing_notification(play)
        except NetworkException as exc:
            logger.exception(f"Error while sending now playing notification: {exc}")
        except ActorRetrievalFailure as exc:
            logger.exception(f"Network service found to be unavailable: {exc}")
            network_service.request_service_restart(self.config)

    def track_playback_ended(self, tl_track: TlTrack, time_position):
        track = tl_track.track
        if not self.is_uri_allowed(track.uri):
            return

        time_position_sec = time_position / 1000
        logger.debug(
            "Advanced-Scrobbler track playback ended after %s: %s",
            int(time_position_sec),
            track.uri,
        )

        db = None
        db_restart_future = None

        try:
            db = db_service.retrieve_service().get(timeout=10)
            correction = db.find_correction(track.uri).get(timeout=10)
        except ActorRetrievalFailure as exc:
            logger.exception(f"Database connection found to be unavailable: {exc}")
            correction = None
            db_restart_future = db_service.request_service_restart(self._global_config)
        except Exception as exc:
            logger.exception(
                f"Error while finding scrobbler correction for track with URI '{track.uri}': {exc}"
            )
            correction = None

        play = prepare_play(track, int(time.time() - time_position_sec), correction)
        if play.duration < 30:
            logger.debug(
                "Advanced-Scrobbler track too short to scrobble (%d secs): %s",
                time_position_sec,
                track.uri,
            )
            return

        threshold = self.config["scrobble_time_threshold"] / 100
        threshold_duration = play.duration * threshold
        if time_position_sec < threshold_duration and time_position_sec < 240:
            logger.debug(
                "Advanced-Scrobbler track not played long enough to scrobble (%d/%d secs): %s",
                time_position_sec,
                play.duration,
                track.uri,
            )
            return

        try:
            if db_restart_future:
                db_restart_future.get(timeout=10)
                db = db_service.retrieve_service().get(timeout=10)

            logger.debug("Advanced-Scrobbler recording finished playback: %s", track.uri)

            db.record_play(play)
        except ActorRetrievalFailure as exc:
            logger.exception(f"Database connection found to be unavailable: {exc}")
        except Exception as exc:
            logger.exception(f"Error while recording play for track with URI '{track.uri}: {exc}")
            raise
