from __future__ import annotations

import logging
from mopidy.http.handlers import StaticFileHandler, check_origin, set_mopidy_headers
import tornado.escape
import tornado.web
from typing import TYPE_CHECKING

from mopidy_advanced_scrobbler.db import db_service, SortDirectionEnum
from mopidy_advanced_scrobbler.models import correction_schema, recorded_play_schema
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
            if content_type != "application/json":
                self.set_status(415, "Content-Type must be application/json")
                return False
        return True

    def set_extra_headers(self):
        super().set_extra_headers()
        self.set_header("Accept", "application/json")
        self.set_header("Content-Type", "application/json; utf-8")


class _BaseJsonPostHandler(_BaseJsonHandler):
    def post(self):
        self.set_extra_headers()
        if not self.check_csrf_protection():
            return

        try:
            data = tornado.escape.json_decode(self.request.body)
        except ValueError as e:
            self.set_status(400, "Invalid request body")
            return

        self._post(data)

    def _post(self, data):
        pass


class ApiLoadPlays(_BaseJsonHandler):
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
            self.set_status(500, "Database connection issue.")
            return

        try:
            plays = db.load_plays(**load_args).get()
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while retrieving plays from database: {exc}")
            self.set_status(500, "Database connection issue.")
            return

        response = {"plays": recorded_play_schema.dump(plays, many=True)}
        self.write(response)


class ApiLoadCorrections(_BaseJsonHandler):
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
            self.set_status(500, "Database connection issue.")
            return

        try:
            corrections = db.load_corrections(**load_args).get()
        except ActorRetrievalFailure as exc:
            logger.exception(f"Error while retrieving corrections from database: {exc}")
            self.set_status(500, "Database connection issue.")
            return

        response = {"corrections": correction_schema.dump(corrections, many=True)}
        self.write(response)
