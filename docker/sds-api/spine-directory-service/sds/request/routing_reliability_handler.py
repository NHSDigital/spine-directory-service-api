from request.base_handler import BaseHandler
from request.content_type_validator import get_valid_accept_type
from request.fhir_json_mapper import get_json_format
from request.fhir_xml_mapper import get_xml_format
from request.http_headers import HttpHeaders
from utilities import timing, integration_adaptors_logger as log

logger = log.IntegrationAdaptorsLogger(__name__)


class RoutingReliabilityRequestHandler(BaseHandler):
    """A handler for requests to obtain combined routing and reliability information."""

    @timing.time_request
    async def get(self):
        org_code = self.get_query_argument("org-code")
        service_id = self.get_query_argument("service-id")
        content_type = get_valid_accept_type(self.request.headers)

        logger.info("Looking up routing and reliability information. {org_code}, {service_id}",
                    fparams={"org_code": org_code, "service_id": service_id})
        routing_and_reliability = await self.routing.get_routing_and_reliability(org_code, service_id)
        logger.info("Obtained routing and reliability information. {routing_and_reliability}",
                    fparams={"routing_and_reliability": routing_and_reliability})

        if content_type == 'application/fhir+xml':
            self.write(get_xml_format(routing_and_reliability, org_code, service_id))
        else:
            self.write(get_json_format(routing_and_reliability, org_code, service_id))
        self.set_header(HttpHeaders.CONTENT_TYPE, content_type)
