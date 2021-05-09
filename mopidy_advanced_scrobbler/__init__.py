import pathlib

import pkg_resources
from mopidy import config, ext

from ._config import Float as ConfigFloat


__version__ = pkg_resources.get_distribution("Mopidy-Advanced-Scrobbler").version


class Extension(ext.Extension):
    dist_name = "Mopidy-Advanced-Scrobbler"
    ext_name = "advanced_scrobbler"
    version = __version__

    def get_default_config(self):
        return config.read(pathlib.Path(__file__).parent / "ext.conf")

    def get_config_schema(self):
        schema = super().get_config_schema()

        schema["api_key"] = config.String()
        schema["api_secret"] = config.Secret()
        schema["username"] = config.String()
        schema["password"] = config.Secret()

        schema["db_timeout"] = config.Integer(optional=True, minimum=1)

        schema["scrobble_time_threshold"] = ConfigFloat(optional=True, minimum=50, maximum=100)

        schema["ignored_uri_schemes"] = config.List(optional=True)

        return schema

    def setup(self, registry):
        from .frontend import AdvancedScrobblerFrontend

        registry.add("frontend", AdvancedScrobblerFrontend)

        registry.add("http:app", {"name": self.ext_name, "factory": self.factory_webapp})

    def factory_webapp(self, config, core):
        from .web import (
            ApiApproveAutoCorrection,
            ApiCorrectionDelete,
            ApiCorrectionEdit,
            ApiCorrectionLoad,
            ApiPlayDelete,
            ApiPlayDeleteMany,
            ApiPlayEdit,
            ApiPlayLoad,
            ApiPlayScrobbleMany,
            ApiPlaySubmit,
            ApiScrobble,
            OverrideStaticFileHandler,
            StaticFileHandler,
        )

        allowed_origins = {origin.lower() for origin in config["http"]["allowed_origins"] if origin}

        path_static = pathlib.Path(__file__).parent / "static"
        path_page_file = path_static / "index.html"

        api_args = {
            "allowed_origins": allowed_origins,
            "csrf_protection": config["http"]["csrf_protection"],
        }
        vue_router_args = {"static_file_path": path_page_file}

        return [
            (r"/css/(.*)", StaticFileHandler, {"path": str(path_static / "css")}),
            (r"/fonts/(.*)", StaticFileHandler, {"path": str(path_static / "fonts")}),
            (r"/js/(.*)", StaticFileHandler, {"path": str(path_static / "js")}),
            (r"/api/plays/load", ApiPlayLoad, api_args),
            (r"/api/plays/edit", ApiPlayEdit, api_args),
            (r"/api/plays/delete", ApiPlayDelete, api_args),
            (r"/api/plays/delete-many", ApiPlayDeleteMany, api_args),
            (r"/api/plays/submit", ApiPlaySubmit, api_args),
            (r"/api/plays/scrobble-many", ApiPlayScrobbleMany, api_args),
            (r"/api/corrections/load", ApiCorrectionLoad, api_args),
            (r"/api/corrections/edit", ApiCorrectionEdit, api_args),
            (r"/api/corrections/delete", ApiCorrectionDelete, api_args),
            (r"/api/approve-auto", ApiApproveAutoCorrection, api_args),
            (r"/api/scrobble", ApiScrobble, api_args),
            (
                r"/favicon\.png$",
                OverrideStaticFileHandler,
                {"static_file_path": path_static / "favicon.png"},
            ),
            (r"/(plays|corrections)", OverrideStaticFileHandler, vue_router_args),
            (r"/", OverrideStaticFileHandler, vue_router_args),
        ]
