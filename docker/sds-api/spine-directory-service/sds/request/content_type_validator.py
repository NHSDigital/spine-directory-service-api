import tornado.web
from comms.http_headers import HttpHeaders
from tornado.httputil import HTTPHeaders
from utilities import integration_adaptors_logger as log

logger = log.IntegrationAdaptorsLogger(__name__)
valid_content_types = ['application/json', 'application/fhir+json', 'application/fhir+xml']


def get_valid_content_type(headers: HTTPHeaders):
    content_type = headers.get(HttpHeaders.CONTENT_TYPE, None)
    if content_type is None:
        return 'application/json'
    elif content_type in valid_content_types:
        return content_type
    else:
        logger.info("Invalid content-type in request")
        raise tornado.web.HTTPError(400, 'Invalid content-type in request',
                                    reason=f'Invalid content-type in request')
