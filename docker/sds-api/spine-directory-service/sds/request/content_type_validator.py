import tornado.web
from tornado.httputil import HTTPHeaders

from request.http_headers import HttpHeaders
from utilities import integration_adaptors_logger as log

logger = log.IntegrationAdaptorsLogger(__name__)
valid_accept_types = ['application/json', 'application/fhir+json', 'application/fhir+xml']


def get_valid_accept_type(headers: HTTPHeaders):
    accept_type = headers.get(HttpHeaders.ACCEPT, 'application/fhir+json').lower()

    if accept_type == '*/*':
        return 'application/fhir+json'
    elif accept_type in valid_accept_types:
        return accept_type
    else:
        logger.info("Invalid content-type in request")
        raise tornado.web.HTTPError(400, 'Invalid Accept header in request',
                                    reason=f'Invalid Accept header in request, only: application/json, '
                                    f'application/fhir+json & application/fhir+xml are allowed')
