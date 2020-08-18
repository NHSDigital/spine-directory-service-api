import tornado.httpserver
import tornado.ioloop
import tornado.web

from request import healthcheck_handler
from utilities import config, secrets
from utilities import integration_adaptors_logger as log

from lookup import sds_client, mhs_attribute_lookup, routing_reliability, \
    sds_connection_factory
from request import routing_reliability_handler

logger = log.IntegrationAdaptorsLogger(__name__)


def initialise_routing(search_base: str) -> routing_reliability.RoutingAndReliability:
    """Initialise the routing and reliability component to be used for SDS queries.

    :param search_base: The LDAP location to use as the base of SDS searched. e.g. ou=services,o=nhs.
    :return:
    """
    sds_connection = sds_connection_factory.create_connection()

    client = sds_client.SDSClient(sds_connection, search_base)
    attribute_lookup = mhs_attribute_lookup.MHSAttributeLookup(client=client)
    routing = routing_reliability.RoutingAndReliability(attribute_lookup)
    return routing


def start_tornado_server(routing: routing_reliability.RoutingAndReliability) -> None:
    """Start the Tornado server

    :param routing: The routing/reliability component to be used when servicing requests.
    """
    handler_dependencies = {"routing": routing}
    application = tornado.web.Application([
        ("/endpoint", routing_reliability_handler.RoutingReliabilityRequestHandler, handler_dependencies),
        ("/healthcheck", healthcheck_handler.HealthcheckHandler)
    ])
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

    routing = initialise_routing(search_base=config.get_config("LDAP_SEARCH_BASE"))
    start_tornado_server(routing)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.critical('Fatal exception in main application', exc_info=True)
    finally:
        logger.info('Exiting application')
