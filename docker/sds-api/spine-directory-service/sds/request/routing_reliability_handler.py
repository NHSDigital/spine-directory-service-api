import json

import tornado
from tornado.web import MissingArgumentError
from urllib.parse import unquote

from request.base_handler import BaseHandler
from request.content_type_validator import get_valid_accept_type
from request.error_handler import ErrorHandler
from request.fhir_json_mapper import build_endpoint_resource, build_bundle_resource
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
        org_code, service_id = self._get_query_params()

        accept_type = get_valid_accept_type(self.request.headers)

        logger.info("Looking up routing and reliability information. {org_code}, {service_id}",
                    fparams={"org_code": org_code, "service_id": service_id})
        all_routing_and_reliability = await self.routing.get_routing_and_reliability(org_code, service_id)
        logger.info("Obtained routing and reliability information. {routing_and_reliability}",
                    fparams={"routing_and_reliability": all_routing_and_reliability})

        endpoints = list(map(lambda routing_and_reliability: build_endpoint_resource(routing_and_reliability, org_code, service_id), all_routing_and_reliability))
        base_url = f"{self.request.protocol}://{self.request.host}{self.request.path}/"
        full_url = unquote(self.request.full_url())
        bundle = build_bundle_resource(endpoints, base_url, full_url)

        # TODO: fix entries being sotred by key. They should be in the creation order
        self.write(json.dumps(bundle, indent=2, sort_keys=False))
        self.set_header(HttpHeaders.CONTENT_TYPE, accept_type)

    @staticmethod
    def _extract_query_parameter_value(value_with_fhir_code, query_parameter_name, fhir_identifier):
        parts = value_with_fhir_code.split("|")
        if len(parts) != 2 or parts[0] != fhir_identifier or len(parts[1]) == 0:
            raise tornado.web.HTTPError(
                status_code=400,
                reason=f"Missing or invalid '{query_parameter_name}' query parameter. Should be '{query_parameter_name}={fhir_identifier}|value'")
        return parts[1]

    def _get_query_params(self):
        org_code_with_fhir_code = self.get_query_argument(ORG_CODE_QUERY_PARAMETER_NAME)
        service_id_with_fhir_code = self.get_query_argument(SERVICE_ID_QUERY_PARAMETER_NAME)

        return (
            self._extract_query_parameter_value(org_code_with_fhir_code, ORG_CODE_QUERY_PARAMETER_NAME, ORG_CODE_FHIR_IDENTIFIER),
            self._extract_query_parameter_value(service_id_with_fhir_code, SERVICE_ID_QUERY_PARAMETER_NAME, SERVICE_ID_FHIR_IDENTIFIER)
        )
