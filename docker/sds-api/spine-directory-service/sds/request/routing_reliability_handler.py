import json

import tornado
from tornado.web import MissingArgumentError
from urllib.parse import unquote

from request.base_handler import BaseHandler, ORG_CODE_QUERY_PARAMETER_NAME, ORG_CODE_FHIR_IDENTIFIER, \
    IDENTIFIER_QUERY_PARAMETER_NAME, SERVICE_ID_FHIR_IDENTIFIER, PARTY_KEY_FHIR_IDENTIFIER
from request.content_type_validator import get_valid_accept_type
from request.error_handler import ErrorHandler
from request.fhir_json_mapper import build_endpoint_resource, build_bundle_resource
from request.http_headers import HttpHeaders
from utilities import timing, integration_adaptors_logger as log, mdc

logger = log.IntegrationAdaptorsLogger(__name__)


class RoutingReliabilityRequestHandler(BaseHandler, ErrorHandler):
    """A handler for requests to obtain combined routing and reliability information."""

    @timing.time_request
    async def get(self):
        org_code = self._get_required_query_param(ORG_CODE_QUERY_PARAMETER_NAME, ORG_CODE_FHIR_IDENTIFIER)
        service_id = self._get_optional_query_param(IDENTIFIER_QUERY_PARAMETER_NAME, SERVICE_ID_FHIR_IDENTIFIER)
        party_key = self._get_optional_query_param(IDENTIFIER_QUERY_PARAMETER_NAME, PARTY_KEY_FHIR_IDENTIFIER)

        if not service_id and not party_key:
            raise tornado.web.HTTPError(
                status_code=400,
                reason=f"Missing or invalid '{IDENTIFIER_QUERY_PARAMETER_NAME}' query parameter. "
                       f"Should be one of or both: ["
                       f"'{IDENTIFIER_QUERY_PARAMETER_NAME}={SERVICE_ID_FHIR_IDENTIFIER}|value', "
                       f"'{IDENTIFIER_QUERY_PARAMETER_NAME}={PARTY_KEY_FHIR_IDENTIFIER}|value'")

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
