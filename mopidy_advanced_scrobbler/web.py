import tornado.web


class IndexHandler(tornado.web.RequestHandler):
    def initialize(self, config, path):
        self.config = config
        self.path = path

    def get(self, path):
        return self.render("index.html", title="Advanced Scrobbler")

    def get_template_path(self):
        return self.path
