from tornado.httputil import HTTPHeaders

from comms.http_headers import HttpHeaders
from utilities import message_utilities, mdc, integration_adaptors_logger as log

logger = log.IntegrationAdaptorsLogger(__name__)


def read_tracking_id_headers(headers: HTTPHeaders):
    _extract_correlation_id(headers)


def _extract_correlation_id(headers: HTTPHeaders):
    correlation_id = headers.get(HttpHeaders.CORRELATION_ID, None)
    if not correlation_id:
        correlation_id = message_utilities.get_uuid()
        logger.info("Didn't receive correlation id in incoming request from supplier, so have generated a new one.")
    mdc.correlation_id.set(correlation_id)
