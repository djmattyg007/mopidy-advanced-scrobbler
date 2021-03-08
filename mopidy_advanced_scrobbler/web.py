from __future__ import annotations

import logging
from mopidy.http.handlers import StaticFileHandler, check_origin, set_mopidy_headers
import tornado.escape
import tornado.httputil
import tornado.web
from typing import TYPE_CHECKING, Optional, Awaitable

from mopidy_advanced_scrobbler.db import db_service, SortDirectionEnum, DbClientError
from mopidy_advanced_scrobbler.models import RecordedPlay, PlayEdit
from mopidy_advanced_scrobbler.models import correction_schema, recorded_play_schema
from mopidy_advanced_scrobbler.network import network_service
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
            if not check_origin(
                origin, self.request.headers, self.allowed_origins
            ):
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

        response = {"success": True, "plays": recorded_play_schema.dump(plays, many=True)}
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
            self.write({"success": False, "message": f"Error after successful scrobble: {str(exc)}"})
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

        response = {"success": True, "corrections": correction_schema.dump(corrections, many=True)}
        self.write(response)
