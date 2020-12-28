import pathlib

import pkg_resources

from mopidy import config, ext
from mopidy.http.handlers import StaticFileHandler

from .schema import Connection


__version__ = pkg_resources.get_distribution("Mopidy-Better-Scrobbler").version


class Extension(ext.Extension):
    dist_name = "Mopidy-Better-Scrobbler"
    ext_name = "better_scrobbler"
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

        return schema

    def setup(self, registry):
        from .frontend import RecorderFrontend

        registry.add("frontend", RecorderFrontend)

        registry.add("http:app", {"name": self.ext_name, "factory": self.factory_webapp})

    def factory_webapp(self, config, core):
        from tornado.web import RedirectHandler
        from .web import IndexHandler

        path_static = pathlib.Path(__file__).parent / "static"
        return [
            (r"/", RedirectHandler, {"url": "index.html"}),
            (r"/index\.html$", IndexHandler, {"config": config, "path": path_static}),
            (r"/(.*)", StaticFileHandler, {"path": path_static})
        ]
