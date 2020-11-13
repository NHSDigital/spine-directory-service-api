import tornado
from tornado.web import MissingArgumentError

from request.base_handler import BaseHandler
from request.content_type_validator import get_valid_accept_type
from request.error_handler import ErrorHandler
from request.fhir_json_mapper import get_json_format
from request.http_headers import HttpHeaders
from utilities import timing, integration_adaptors_logger as log

logger = log.IntegrationAdaptorsLogger(__name__)

ORG_CODE_QUERY_PARAMETER_NAME = "organization"
SERVICE_ID_QUERY_PARAMETER_NAME = "identifier"

ORG_CODE_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/ods-organization-code"
SERVICE_ID_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/nhsEndpointServiceId"


class RoutingReliabilityRequestHandler(BaseHandler, ErrorHandler):
    """A handler for requests to obtain combined routing and reliability information."""

    def prepare(self):
        if self.request.method != "GET":
            raise tornado.web.HTTPError(
                status_code=405,
                reason="Method not allowed.")

    @timing.time_request
    async def get(self):
        org_code = self.get_org_code()
        service_id = self.get_service_id()

        accept_type = get_valid_accept_type(self.request.headers)

        logger.info("Looking up routing and reliability information. {org_code}, {service_id}",
                    fparams={"org_code": org_code, "service_id": service_id})
        routing_and_reliability = await self.routing.get_routing_and_reliability(org_code, service_id)
        logger.info("Obtained routing and reliability information. {routing_and_reliability}",
                    fparams={"routing_and_reliability": routing_and_reliability})

        self.write(get_json_format(routing_and_reliability, org_code, service_id))
        self.set_header(HttpHeaders.CONTENT_TYPE, accept_type)

    def _get_query_parameter(self, query_parameter_name, fhir_identifier):
        value = self.get_query_argument(query_parameter_name)
        parts = value.split("|")
        if len(parts) != 2 or parts[0] != fhir_identifier or len(parts[1]) == 0:
            raise tornado.web.HTTPError(
                status_code=400,
                reason=f"Missing or invalid '{query_parameter_name}' query parameter. Should be '{query_parameter_name}={fhir_identifier}|value'")

        return parts[1]

    def get_org_code(self):
        return self._get_query_parameter(ORG_CODE_QUERY_PARAMETER_NAME, ORG_CODE_FHIR_IDENTIFIER)

    def get_service_id(self):
        return self._get_query_parameter(SERVICE_ID_QUERY_PARAMETER_NAME, SERVICE_ID_FHIR_IDENTIFIER)
