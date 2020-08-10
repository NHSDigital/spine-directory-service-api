from request.base_handler import BaseHandler
from request.content_type_validator import get_valid_accept_type
from request.http_headers import HttpHeaders
from utilities import timing, integration_adaptors_logger as log

logger = log.IntegrationAdaptorsLogger(__name__)


class RoutingRequestHandler(BaseHandler):
    """A handler for requests to obtain routing information."""

    @timing.time_request
    async def get(self):
        org_code = self.get_query_argument("org-code")
        service_id = self.get_query_argument("service-id")
        content_type = get_valid_accept_type(self.request.headers)

        logger.info("Looking up routing information. {org_code}, {service_id}",
                    fparams={"org_code": org_code, "service_id": service_id})
        routing_info = await self.routing.get_end_point(org_code, service_id)
        logger.info("Obtained routing information. {routing_information}",
                    fparams={"routing_information": routing_info})

        self.write(routing_info)
        self.set_header(HttpHeaders.CONTENT_TYPE, content_type)
