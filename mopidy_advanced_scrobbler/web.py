from __future__ import annotations

import logging
from time import sleep
from typing import TYPE_CHECKING, List, Optional

import tornado.escape
import tornado.httputil
import tornado.web
from mopidy.http.handlers import StaticFileHandler, check_origin, set_mopidy_headers

from mopidy_advanced_scrobbler.db import DbClientError, SortDirectionEnum, db_service
from mopidy_advanced_scrobbler.models import (
    CorrectionEdit,
    PlayEdit,
    RecordedPlay,
    correction_schema,
    recorded_play_schema,
)
from mopidy_advanced_scrobbler.network import NetworkException, network_service

from ._service import ActorRetrievalFailure


if TYPE_CHECKING:
    from pathlib import Path


logger = logging.getLogger(__name__)


class OverrideStaticFileHandler(StaticFileHandler):
    def initialize(self, static_file_path: Path):
        self.static_file_path = str(static_file_path)
        super().initialize(str(static_file_path.parent))

    def get(self, path=None, include_body=True):
        return super().get(self.static_file_path, include_body)


class _BaseHandler(tornado.web.RequestHandler):
    def initialize(self, allowed_origins, csrf_protection):
        self.allowed_origins = allowed_origins
        self.csrf_protection = csrf_protection

    def head(self):
        self.set_extra_headers()

    def options(self):
        self.set_extra_headers()
        if self.csrf_protection:
            origin = self.request.headers.get("Origin")
            if not check_origin(origin, self.request.headers, self.allowed_origins):
                self.set_status(403, f"Access denied for origin {origin}")
                return

            self.set_header("Access-Control-Allow-Origin", f"{origin}")
            self.set_header("Access-Control-Allow-Headers", "Content-Type")

        self.set_status(204)

    def set_extra_headers(self):
        set_mopidy_headers(self)


class _BaseJsonHandler(_BaseHandler):
    def check_csrf_protection(self):
        if self.csrf_protection:
            content_type = self.request.headers.get("Content-Type", "")
            if content_type:
                content_type, _ = tornado.httputil._parse_header(content_type)
            if content_type != "application/json":
                self.set_status(415)
                self.write({"success": False, "message": "Content-Type must be application/json"})
                return False
        return True

    def set_extra_headers(self):
        super().set_extra_headers()
        self.set_header("Accept", "application/json")
        self.set_header("Content-Type", "application/json; utf-8")

    def compute_etag(self):
        return None


class _BaseJsonPostHandler(_BaseJsonHandler):
    def post(self):
        self.set_extra_headers()
        if not self.check_csrf_protection():
            return

        try:
            data = tornado.escape.json_decode(self.request.body)
        except ValueError:
            self.set_status(400)
            self.write({"success": False, "message": "Invalid request body"})
            return

        self._post(data)

    def _post(self, data):
        raise NotImplementedError()


class ApiPlayLoad(_BaseJsonHandler):
    def get(self):
        self.set_extra_headers()
        load_args = {}

        try:
            sort_direction = SortDirectionEnum(self.get_query_argument("sort", ""))
            load_args["sort_direction"] = sort_direction
        except ValueError:
            pass

        try:
            page_num = int(self.get_query_argument("page", ""))
            load_args["page_num"] = max(page_num, 1)
        except ValueError:
            pass

        try:
            page_size = int(self.get_query_argument("page_size", ""))
            load_args["page_size"] = max(min(page_size, 100), 1)
        except ValueError:
            pass

        try:
            db = db_service.retrieve_service().get()
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while retrieving database service: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Database connection issue."})
            return

        try:
            plays = db.load_plays(**load_args).get()
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while retrieving plays from database: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Database connection issue."})
            return

        overall_plays_count = -1
        unsubmitted_plays_count = -1
        try:
            overall_plays_count = db.get_plays_count().get()
            unsubmitted_plays_count = db.get_plays_count(only_unsubmitted=True).get()
        except Exception as exc:
            logger.exception(f"Error while retrieving play counts from database: {exc}")

        response = {
            "success": True,
            "plays": recorded_play_schema.dump(plays, many=True),
            "counts": {
                "overall": overall_plays_count,
                "unsubmitted": unsubmitted_plays_count,
            },
        }
        self.write(response)


class ApiPlayEdit(_BaseJsonPostHandler):
    def _post(self, data):
        if "play" not in data:
            self.set_status(400)
            self.write({"success": False, "message": "Missing play data."})
            return

        try:
            play_edit = PlayEdit.from_dict(data["play"])
        except Exception:
            self.set_status(400)
            self.write({"success": False, "message": "Invalid play data."})
            return

        try:
            db = db_service.retrieve_service().get()
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while retrieving database service: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Database connection issue."})
            return

        try:
            db.edit_play(play_edit).get()
        except DbClientError as exc:
            self.set_status(400)
            self.write({"success": False, "message": str(exc)})
            return
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while editing play: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Database connection issue."})
            return

        self.write({"success": True})


class ApiPlayDelete(_BaseJsonPostHandler):
    def _post(self, data):
        if "playId" not in data:
            self.set_status(400)
            self.write({"success": False, "message": "Missing play ID."})
            return

        try:
            play_id = int(data["playId"])
        except Exception:
            self.set_status(400)
            self.write({"success": False, "message": "Invalid play ID."})
            return

        try:
            db = db_service.retrieve_service().get()
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while retrieving database service: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Database connection issue."})
            return

        try:
            success = db.delete_play(play_id).get()
        except DbClientError as exc:
            self.set_status(400)
            self.write({"success": False, "message": str(exc)})
            return
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while deleting play: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Database connection issue."})
            return

        self.write({"success": success})


class ApiPlayDeleteMany(_BaseJsonPostHandler):
    def _post(self, data):
        if "playIds" not in data:
            self.set_status(400)
            self.write({"success": False, "message": "Missing play IDs."})
            return

        try:
            if not isinstance(data["playIds"], list):
                raise ValueError()
            play_ids = tuple(map(int, data["playIds"]))
        except Exception:
            self.set_status(400)
            self.write({"success": False, "message": "Invalid play IDs."})
            return

        try:
            db = db_service.retrieve_service().get()
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while retrieving database service: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Database connection issue."})
            return

        try:
            db.delete_plays(play_ids).get()
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while deleting plays: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Database connection issue."})
            return

        self.write({"success": True})


class ApiPlaySubmit(_BaseJsonPostHandler):
    def _post(self, data):
        if "playId" not in data:
            self.set_status(400)
            self.write({"success": False, "message": "Missing play ID."})
            return

        try:
            play_id = int(data["playId"])
        except Exception:
            self.set_status(400)
            self.write({"success": False, "message": "Invalid play ID."})
            return

        try:
            db = db_service.retrieve_service().get()
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while retrieving database service: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Database connection issue."})
            return

        try:
            play: RecordedPlay = db.find_play(play_id).get()
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while finding play in database: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Database connection issue."})
            return

        if not play:
            self.set_status(400)
            self.write({"success": False, "message": "Play does not exist."})
            return
        elif play.submitted_at:
            self.set_status(400)
            self.write({"success": False, "message": "Play was already submitted."})
            return

        try:
            network = network_service.retrieve_service().get()
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while retrieving network service: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Last.fm connection issue."})
            return

        try:
            network.submit_scrobble(play).get()
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while scrobbling play: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Last.fm connection issue."})
            return

        try:
            success = db.mark_play_submitted(play.play_id).get()
        except DbClientError as exc:
            self.set_status(400)
            self.write({"success": False, "message": f"Error after successful scrobble: {exc}"})
            return
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while marking play as submitted: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Database connection issue after ."})
            return

        self.write({"success": success})


class ApiCorrectionLoad(_BaseJsonHandler):
    def get(self):
        self.set_extra_headers()
        load_args = {}

        try:
            page_num = int(self.get_query_argument("page", ""))
            load_args["page_num"] = max(page_num, 1)
        except ValueError:
            pass

        try:
            page_size = int(self.get_query_argument("page_size", ""))
            load_args["page_size"] = max(min(page_size, 100), 1)
        except ValueError:
            pass

        try:
            db = db_service.retrieve_service().get()
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while retrieving database service: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Database connection issue."})
            return

        try:
            corrections = db.load_corrections(**load_args).get()
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while retrieving corrections from database: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Database connection issue."})
            return

        overall_corrections_count = -1
        try:
            overall_corrections_count = db.get_corrections_count().get()
        except Exception as exc:
            logger.exception(f"Error while retrieving play counts from database: {exc}")

        response = {
            "success": True,
            "corrections": correction_schema.dump(corrections, many=True),
            "counts": {
                "overall": overall_corrections_count,
            },
        }
        self.write(response)


class ApiCorrectionEdit(_BaseJsonPostHandler):
    def _post(self, data):
        if "correction" not in data:
            self.set_status(400)
            self.write({"success": False, "message": "Missing correction data."})
            return

        try:
            correction_edit = CorrectionEdit.from_dict(data["correction"])
        except Exception:
            self.set_status(400)
            self.write({"success": False, "message": "Invalid correction data."})
            return

        try:
            db = db_service.retrieve_service().get()
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while retrieving database service: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Database connection issue."})
            return

        try:
            db.edit_correction(correction_edit).get()
        except DbClientError as exc:
            self.set_status(400)
            self.write({"success": False, "message": str(exc)})
            return
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while editing correction: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Database connection issue."})
            return

        self.write({"success": True})


class ApiCorrectionDelete(_BaseJsonPostHandler):
    def _post(self, data):
        if "trackUri" not in data:
            self.set_status(400)
            self.write({"success": False, "message": "Missing track URI."})
            return

        try:
            track_uri = str(data["trackUri"])
        except Exception:
            self.set_status(400)
            self.write({"success": False, "message": "Invalid track URI."})
            return

        try:
            db = db_service.retrieve_service().get()
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while retrieving database service: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Database connection issue."})
            return

        try:
            success = db.delete_correction(track_uri).get()
        except DbClientError as exc:
            self.set_status(400)
            self.write({"success": False, "message": str(exc)})
            return
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while deleting correction: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Database connection issue."})
            return

        self.write({"success": success})


class ApiApproveAutoCorrection(_BaseJsonPostHandler):
    def _post(self, data):
        if "playId" not in data:
            self.set_status(400)
            self.write({"success": False, "message": "Missing play ID."})
            return

        try:
            play_id = int(data["playId"])
        except Exception:
            self.set_status(400)
            self.write({"success": False, "message": "Invalid play ID."})
            return

        try:
            db = db_service.retrieve_service().get()
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while retrieving database service: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Database connection issue."})
            return

        try:
            db.approve_auto_correction(play_id).get()
        except DbClientError as exc:
            self.set_status(400)
            self.write({"success": False, "message": str(exc)})
            return
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while approving auto-correction: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Database connection issue."})
            return

        self.write({"success": True})


class ApiPlayScrobbleMany(_BaseJsonPostHandler):
    def _post(self, data):
        if "playIds" not in data:
            self.set_status(400)
            self.write({"success": False, "message": "Missing play IDs."})
            return

        try:
            if not isinstance(data["playIds"], list):
                raise ValueError()
            play_ids = tuple(map(int, data["playIds"]))
        except Exception:
            self.set_status(400)
            self.write({"success": False, "message": "Invalid play IDs."})
            return

        try:
            db = db_service.retrieve_service().get()
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while retrieving database service: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Database connection issue."})
            return

        try:
            network = network_service.retrieve_service().get()
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while retrieving network service: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Last.fm connection issue."})
            return

        found_plays: List[int] = []
        scrobbled_plays: List[int] = []
        marked_plays: List[int] = []
        err_msg: Optional[str] = None
        for batch_start_id in range(0, 250, 50):
            play_ids_batch = play_ids[batch_start_id : batch_start_id + 50]

            try:
                unsubmitted_plays = db.find_plays(play_ids_batch, only_unsubmitted=True).get()
            except ActorRetrievalFailure as exc:
                logger.exception(f"Error while retrieving unsubmitted plays: {exc}")
                err_msg = "Error while retrieving unsubmitted plays."
                break

            if not unsubmitted_plays:
                break

            unsubmitted_play_ids = tuple(map(lambda play: play.play_id, unsubmitted_plays))
            found_plays.extend(unsubmitted_play_ids)

            try:
                network.submit_scrobbles(unsubmitted_plays).get()
            except NetworkException as exc:
                logger.exception(f"Network error while scrobbling plays: {exc}")
                err_msg = "Network error while scrobbling plays."
                break
            except ActorRetrievalFailure as exc:
                logger.exception(f"Error while scrobbling plays: {exc}")
                err_msg = "Error while scrobbling plays."
                break

            scrobbled_plays.extend(unsubmitted_play_ids)

            try:
                db.mark_plays_submitted(unsubmitted_play_ids).get()
            except DbClientError as exc:
                logger.exception(f"Error after successful scrobble: {exc}")
                err_msg = "Error after successful scrobble."
                break
            except ActorRetrievalFailure as exc:
                logger.exception(f"Error while marking plays as submitted: {exc}")
                err_msg = "Error while marking plays as submitted."
                break
            except Exception as exc:
                logger.exception(f"Error while marking plays as submitted: {exc}")
                err_msg = "Error while marking plays as submitted."
                break

            marked_plays.extend(unsubmitted_play_ids)
            # Vague rate-limiting of requests to the Network API
            sleep(1)

        self.write(
            {
                "success": True,
                "foundPlays": found_plays,
                "scrobbledPlays": scrobbled_plays,
                "markedPlays": marked_plays,
                "message": err_msg,
            }
        )


class ApiScrobble(_BaseJsonPostHandler):
    def _post(self, data):
        if "checkpoint" in data:
            try:
                checkpoint = int(data["checkpoint"])
            except Exception:
                self.set_status(400)
                self.write({"success": False, "message": "Invalid checkpoint."})
                return
        else:
            checkpoint = None

        try:
            db = db_service.retrieve_service().get()
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while retrieving database service: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Database connection issue."})
            return

        try:
            network = network_service.retrieve_service().get()
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while retrieving network service: {exc}")
            self.set_status(500)
            self.write({"success": False, "message": "Last.fm connection issue."})
            return

        found_plays: List[int] = []
        scrobbled_plays: List[int] = []
        marked_plays: List[int] = []
        err_msg: Optional[str] = None
        for _ in range(0, 5):
            try:
                unsubmitted_plays = db.load_unsubmitted_plays_batch(checkpoint=checkpoint).get()
            except ActorRetrievalFailure as exc:
                logger.exception(f"Error while retrieving unsubmitted plays: {exc}")
                err_msg = "Error while retrieving unsubmitted plays."
                break

            if not unsubmitted_plays:
                break

            unsubmitted_play_ids = tuple(map(lambda play: play.play_id, unsubmitted_plays))
            found_plays.extend(unsubmitted_play_ids)

            try:
                network.submit_scrobbles(unsubmitted_plays).get()
            except NetworkException as exc:
                logger.exception(f"Network error while scrobbling plays: {exc}")
                err_msg = "Network error while scrobbling plays."
                break
            except ActorRetrievalFailure as exc:
                logger.exception(f"Error while scrobbling plays: {exc}")
                err_msg = "Error while scrobbling plays."
                break

            scrobbled_plays.extend(unsubmitted_play_ids)

            try:
                db.mark_plays_submitted(unsubmitted_play_ids).get()
            except DbClientError as exc:
                logger.exception(f"Error after successful scrobble: {exc}")
                err_msg = "Error after successful scrobble."
                break
            except ActorRetrievalFailure as exc:
                logger.exception(f"Error while marking plays as submitted: {exc}")
                err_msg = "Error while marking plays as submitted."
                break
            except Exception as exc:
                logger.exception(f"Error while marking plays as submitted: {exc}")
                err_msg = "Error while marking plays as submitted."
                break

            marked_plays.extend(unsubmitted_play_ids)
            # Vague rate-limiting of requests to the Network API
            sleep(1)

        self.write(
            {
                "success": True,
                "foundPlays": found_plays,
                "scrobbledPlays": scrobbled_plays,
                "markedPlays": marked_plays,
                "message": err_msg,
            }
        )
