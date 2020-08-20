from request.base_handler import BaseHandler
from request.content_type_validator import get_valid_accept_type
from request.http_headers import HttpHeaders
from request.fhir_json_mapper import get_json_format
from request.fhir_xml_mapper import get_xml_format
from utilities import timing, integration_adaptors_logger as log

logger = log.IntegrationAdaptorsLogger(__name__)


class RoutingReliabilityRequestHandler(BaseHandler):
    """A handler for requests to obtain combined routing and reliability information."""

    @timing.time_request
    async def get(self):
        org_code = self.get_query_argument("org-code")
        service_id = self.get_query_argument("service-id")
        content_type = get_valid_accept_type(self.request.headers)

        # TODO: could be run in parallel

        logger.info("Looking up routing information. {org_code}, {service_id}",
                    fparams={"org_code": org_code, "service_id": service_id})
        routing_info = await self.routing.get_end_point(org_code, service_id)
        logger.info("Obtained routing information. {routing_information}",
                    fparams={"routing_information": routing_info})

        logger.info("Looking up reliability information. {org_code}, {service_id}",
                    fparams={"org_code": org_code, "service_id": service_id})
        reliability_info = await self.routing.get_reliability(org_code, service_id)
        logger.info("Obtained reliability information. {reliability_information}",
                    fparams={"reliability_information": reliability_info})

        combined_info = {**routing_info, **reliability_info}
        logger.info("Combined routing and reliability information. {routing_reliability_information}",
                    fparams={"routing_reliability_information": combined_info})

        if content_type == 'application/fhir+xml':
            self.write(get_xml_format(combined_info, org_code, service_id))
        else:
            self.write(get_json_format(combined_info, org_code, service_id))
        self.set_header(HttpHeaders.CONTENT_TYPE, content_type)
