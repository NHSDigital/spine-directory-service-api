from typing import Optional, Dict, Any

import logging
import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado import httputil
from tornado.routing import Matcher

import lookup.sds_client_factory
from lookup import mhs_attribute_lookup, routing_reliability
from request import healthcheck_handler
from request import routing_reliability_handler
from request.error_handler import ErrorHandler
from utilities import config, secrets
from utilities import integration_adaptors_logger as log
from ldap3.utils.log import set_library_log_activation_level, set_library_log_detail_level, EXTENDED

logger = log.IntegrationAdaptorsLogger(__name__)
set_library_log_detail_level(EXTENDED)
set_library_log_activation_level(logging.CRITICAL)

def initialise_routing() -> routing_reliability.RoutingAndReliability:
    """Initialise the routing and reliability component to be used for SDS queries.

    :return:
    """
    client = lookup.sds_client_factory.get_sds_client()
    attribute_lookup = mhs_attribute_lookup.MHSAttributeLookup(client=client)
    routing = routing_reliability.RoutingAndReliability(attribute_lookup)
    return routing


def start_tornado_server(routing: routing_reliability.RoutingAndReliability) -> None:
    """Start the Tornado server

    :param routing: The routing/reliability component to be used when servicing requests.
    """

    class CaseInsensitiveRouteMatcher(Matcher):
        def __init__(self, path) -> None:
            super().__init__()
            self.path = path

        def match(self, request: httputil.HTTPServerRequest) -> Optional[Dict[str, Any]]:
            return {} if request.path.lower() == self.path.lower() else None

    handler_dependencies = {"routing": routing}
    application = tornado.web.Application([
        (CaseInsensitiveRouteMatcher("/endpoint"), routing_reliability_handler.RoutingReliabilityRequestHandler, handler_dependencies),
        (CaseInsensitiveRouteMatcher("/healthcheck"), healthcheck_handler.HealthcheckHandler)
    ], default_handler_class=ErrorHandler)
    server = tornado.httpserver.HTTPServer(application)
    server_port = int(config.get_config('SERVER_PORT', default='9000'))
    server.listen(server_port)

    logger.info('Starting router server at port {server_port}', fparams={'server_port': server_port})
    tornado_io_loop = tornado.ioloop.IOLoop.current()
    try:
        tornado_io_loop.start()
    except KeyboardInterrupt:
        logger.warning('Keyboard interrupt')
        pass
    finally:
        tornado_io_loop.stop()
        tornado_io_loop.close(True)
    logger.info('Server shut down, exiting...')


def main():
    config.setup_config("SDS")
    secrets.setup_secret_config("SDS")
    log.configure_logging('sds')

    routing = initialise_routing()
    start_tornado_server(routing)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.critical('Fatal exception in main application', exc_info=True)
    finally:
        logger.info('Exiting application')
