import tornado.web

from lookup import routing_reliability
from utilities import mdc, message_utilities


class BaseHandler(tornado.web.RequestHandler):
    """A base handler for spine route lookup"""

    def initialize(self, routing: routing_reliability.RoutingAndReliability) -> None:
        """Initialise this request handler with the provided configuration values.

        :param routing: The routing and reliability component to use to look up values in SDS.
        """
        mdc.trace_id.set(message_utilities.get_uuid())
        self.routing = routing
