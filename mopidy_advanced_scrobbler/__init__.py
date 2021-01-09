import pathlib

import pkg_resources

from mopidy import config, ext
from mopidy.http.handlers import StaticFileHandler

from ._config import Float as ConfigFloat
from .schema import Connection


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

        schema["ignored_uri_schemes"] = config.List()

        return schema

    def setup(self, registry):
        from .frontend import AdvancedScrobblerFrontend

        registry.add("frontend", AdvancedScrobblerFrontend)

        registry.add("http:app", {"name": self.ext_name, "factory": self.factory_webapp})

    def factory_webapp(self, config, core):
        from tornado.web import RedirectHandler

        path_static = pathlib.Path(__file__).parent / "static"
        return [
            (r"/", RedirectHandler, {"url": "index.html"}),
            (r"/(.*)", StaticFileHandler, {"path": path_static}),
        ]
