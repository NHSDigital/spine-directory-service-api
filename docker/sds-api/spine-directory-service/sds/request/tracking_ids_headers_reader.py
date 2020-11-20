import re

import tornado
from tornado.httputil import HTTPHeaders

from request.http_headers import HttpHeaders
from utilities import message_utilities, mdc, integration_adaptors_logger as log

logger = log.IntegrationAdaptorsLogger(__name__)

UUID_PATTERN = "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"


def read_tracking_id_headers(headers: HTTPHeaders):
    _extract_correlation_id(headers)


def _extract_correlation_id(headers: HTTPHeaders):
    correlation_id = headers.get(HttpHeaders.X_CORRELATION_ID, None)

    if not correlation_id:
        correlation_id = message_utilities.get_uuid()
        logger.info(f"Request is missing {HttpHeaders.X_CORRELATION_ID} header. Assigning new value: {correlation_id}")
    else:
        if len(re.findall(UUID_PATTERN, correlation_id)) != 1:
            raise tornado.web.HTTPError(
                status_code=400,
                reason=f"Invalid {HttpHeaders.X_CORRELATION_ID} header. Should be an UUIDv4 matching regex '{UUID_PATTERN}'")

    mdc.correlation_id.set(correlation_id)
