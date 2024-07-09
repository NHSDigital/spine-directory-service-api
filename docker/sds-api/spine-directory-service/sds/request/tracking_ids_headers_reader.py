import re

import tornado
from tornado.httputil import HTTPHeaders

from request.http_headers import HttpHeaders
from utilities import message_utilities, mdc, integration_adaptors_logger as log

logger = log.IntegrationAdaptorsLogger(__name__)

UUID_PATTERN = "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"

def _get_or_create_correlation_id(headers: HTTPHeaders, raise_error=True) -> str:
    correlation_id = headers.get(HttpHeaders.X_CORRELATION_ID, None)
    if not correlation_id:
        correlation_id = message_utilities.get_uuid()
        logger.info(f"Request is missing {HttpHeaders.X_CORRELATION_ID} header. Assigning new value: {correlation_id}")
    else:
        if len(re.findall(UUID_PATTERN, correlation_id)) != 1:
            if raise_error:
                raise tornado.web.HTTPError(
                    status_code=400,
                    log_message=f"Invalid {HttpHeaders.X_CORRELATION_ID} header. Should be an UUIDv4 matching regex '{UUID_PATTERN}'")
            else:
                correlation_id = message_utilities.get_uuid()
                logger.info(f"Invalid {HttpHeaders.X_CORRELATION_ID} header. Assigning new value: {correlation_id}")
    return correlation_id



def read_tracking_id_headers(headers: HTTPHeaders, raise_error=True):
    x_correlation_id = mdc.correlation_id.get() or _get_or_create_correlation_id(headers=headers, raise_error=raise_error)
    mdc.correlation_id.set(x_correlation_id)

    tracking_id_headers = {HttpHeaders.X_CORRELATION_ID: x_correlation_id}

    x_request_id = headers.get(HttpHeaders.X_REQUEST_ID, None)
    if x_request_id:
        tracking_id_headers[HttpHeaders.X_REQUEST_ID] = x_request_id

    return tracking_id_headers
