import json

import tornado
from tornado.web import MissingArgumentError
from urllib.parse import unquote

from request.base_handler import BaseHandler
from request.content_type_validator import get_valid_accept_type
from request.error_handler import ErrorHandler
from request.fhir_json_mapper import build_endpoint_resource, build_bundle_resource
from request.http_headers import HttpHeaders
from request.tracking_ids_headers_reader import read_tracking_id_headers
from utilities import timing, integration_adaptors_logger as log, mdc

logger = log.IntegrationAdaptorsLogger(__name__)

ORG_CODE_QUERY_PARAMETER_NAME = "organization"
IDENTIFIER_QUERY_PARAMETER_NAME = "identifier"

ORG_CODE_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/ods-organization-code"
SERVICE_ID_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/nhsEndpointServiceId"
PARTY_KEY_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/nhsMhsPartyKey"

VALID_IDENTIFIERS = [
    SERVICE_ID_FHIR_IDENTIFIER,
    PARTY_KEY_FHIR_IDENTIFIER
]


class RoutingReliabilityRequestHandler(BaseHandler, ErrorHandler):
    """A handler for requests to obtain combined routing and reliability information."""

    def prepare(self):
        if self.request.method != "GET":
            raise tornado.web.HTTPError(
                status_code=405,
                log_message="Method not allowed.")

    @timing.time_request
    async def get(self):
        read_tracking_id_headers(self.request.headers)

        org_code = self._get_org_code_query_param()
        service_id, party_key = self._get_identifiers_from_query_params()

        accept_type = get_valid_accept_type(self.request.headers)

        logger.info("Looking up routing and reliability information. {org_code}, {service_id}",
                    fparams={"org_code": org_code, "service_id": service_id})
        ldap_result = await self.routing.get_routing_and_reliability(org_code, service_id, party_key)
        logger.info("Obtained routing and reliability information. {ldap_result}",
                    fparams={"ldap_result": ldap_result})

        base_url = f"{self.request.protocol}://{self.request.host}{self.request.path}/"
        full_url = unquote(self.request.full_url())

        endpoints = []
        for ldap_attributes in ldap_result:
            endpoints += build_endpoint_resource(ldap_attributes, org_code, service_id)

        bundle = build_bundle_resource(endpoints, base_url, full_url)

        self.write(json.dumps(bundle, indent=2, sort_keys=False))
        self.set_header(HttpHeaders.CONTENT_TYPE, accept_type)
        self.set_header(HttpHeaders.X_CORRELATION_ID, mdc.correlation_id.get())

    def _get_org_code_query_param(self):
        value = self.get_query_argument(ORG_CODE_QUERY_PARAMETER_NAME)
        parts = value.split("|")
        if len(parts) != 2 or parts[0] != ORG_CODE_FHIR_IDENTIFIER or not parts[1]:
            raise tornado.web.HTTPError(
                status_code=400,
                reason=f"Missing or invalid '{ORG_CODE_QUERY_PARAMETER_NAME}' query parameter. Should be '{ORG_CODE_QUERY_PARAMETER_NAME}={ORG_CODE_FHIR_IDENTIFIER}|value'")
        return value[value.index("|") + 1:]

    def _get_identifiers_from_query_params(self):
        identifiers_with_fhir_code = list(filter(
            lambda identifier: "|" in identifier and identifier.split("|")[0] in VALID_IDENTIFIERS and identifier.split("|")[1],
            self.get_query_arguments(IDENTIFIER_QUERY_PARAMETER_NAME)))

        if len(identifiers_with_fhir_code) == 0:
            raise tornado.web.HTTPError(
                status_code=400,
                reason=f"Missing or invalid '{IDENTIFIER_QUERY_PARAMETER_NAME}' query parameter. "
                       f"Should be '{IDENTIFIER_QUERY_PARAMETER_NAME}={SERVICE_ID_FHIR_IDENTIFIER}|value'"
                       f"or '{IDENTIFIER_QUERY_PARAMETER_NAME}={PARTY_KEY_FHIR_IDENTIFIER}|value'")

        service_id = list(filter(lambda identifier: identifier.startswith(SERVICE_ID_FHIR_IDENTIFIER), identifiers_with_fhir_code))
        service_id = service_id and service_id[-1]
        service_id = (service_id and service_id[service_id.index("|") + 1:]) or None
        party_key = list(filter(lambda identifier: identifier.startswith(PARTY_KEY_FHIR_IDENTIFIER), identifiers_with_fhir_code))
        party_key = party_key and party_key[-1]
        party_key = (party_key and party_key[party_key.index("|") + 1:]) or None

        return service_id, party_key
