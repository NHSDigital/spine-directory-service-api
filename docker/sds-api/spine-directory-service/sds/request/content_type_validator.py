import tornado.web
from tornado.httputil import HTTPHeaders

from request.http_headers import HttpHeaders
from utilities import integration_adaptors_logger as log

logger = log.IntegrationAdaptorsLogger(__name__)

APPLICATION_JSON = 'application/json'
APPLICATION_FHIR_JSON = 'application/fhir+json'

valid_accept_types = [APPLICATION_JSON, APPLICATION_FHIR_JSON]


def get_valid_accept_type(headers: HTTPHeaders):
    accept_type = headers.get(HttpHeaders.ACCEPT, APPLICATION_FHIR_JSON).lower()

    if accept_type == '*/*':
        return APPLICATION_FHIR_JSON
    elif accept_type in valid_accept_types:
        return accept_type
    else:
        logger.info("Invalid Accept header in request")
        raise tornado.web.HTTPError(406, 'Invalid Accept header in request',
                                    reason=f'Invalid Accept header in request, only: ' + str(valid_accept_types) + ' are allowed')
