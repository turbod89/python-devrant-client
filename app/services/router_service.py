from .logging import logging


class RouterService(object):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._routes = {}

    def register_route(self, name, f):
        self._routes[name] = f
        return self

    def navigate_to(self, name, *args, **kwargs):
        f = self._routes.get(name)
        if f is None:
            logging.error("Route named '{}' is not registered.".format(name))
        else:
            f(*args, **kwargs)
        return self
