import json

import tornado
from tornado.web import MissingArgumentError
from urllib.parse import unquote

from request.base_handler import BaseHandler, ORG_CODE_QUERY_PARAMETER_NAME, ORG_CODE_FHIR_IDENTIFIER, \
    IDENTIFIER_QUERY_PARAMETER_NAME, SERVICE_ID_FHIR_IDENTIFIER, PARTY_KEY_FHIR_IDENTIFIER
from request.content_type_validator import get_valid_accept_type
from request.error_handler import ErrorHandler
from request.fhir_json_mapper import build_endpoint_resources, build_bundle_resource
from request.http_headers import HttpHeaders
from request.tracking_ids_headers_reader import read_tracking_id_headers
from utilities import timing, integration_adaptors_logger as log, mdc

logger = log.IntegrationAdaptorsLogger(__name__)


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

        self._validate_query_params()

        org_code = self.get_optional_query_param(ORG_CODE_QUERY_PARAMETER_NAME, ORG_CODE_FHIR_IDENTIFIER)
        service_id = self.get_optional_query_param(IDENTIFIER_QUERY_PARAMETER_NAME, SERVICE_ID_FHIR_IDENTIFIER)
        party_key = self.get_optional_query_param(IDENTIFIER_QUERY_PARAMETER_NAME, PARTY_KEY_FHIR_IDENTIFIER)

        if org_code:
            if not service_id and not party_key:
                self._raise_invalid_query_params_error()
        else:
            if not service_id or not party_key:
                self._raise_invalid_query_params_error()

        accept_type = get_valid_accept_type(self.request.headers)

        logger.info("Looking up routing and reliability information. {org_code}, {service_id}, {party_key}",
                    fparams={"org_code": org_code, "service_id": service_id, "party_key": party_key})
        ldap_result = await self.sds_client.get_mhs_details(org_code, service_id, party_key)
        logger.info("Obtained routing and reliability information. {ldap_result}",
                    fparams={"ldap_result": ldap_result})

        base_url = f"{self.request.protocol}://{self.request.host}{self.request.path}/"
        full_url = unquote(self.request.full_url())

        endpoints = []
        for ldap_attributes in ldap_result:
            endpoints += build_endpoint_resources(ldap_attributes)

        bundle = build_bundle_resource(endpoints, base_url, full_url)

        self.write(json.dumps(bundle, indent=2, sort_keys=False))
        self.set_header(HttpHeaders.CONTENT_TYPE, accept_type)
        self.set_header(HttpHeaders.X_CORRELATION_ID, mdc.correlation_id.get())

    def _validate_query_params(self):
        query_params = self.request.arguments
        for query_param in query_params.keys():
            if query_param not in [ORG_CODE_QUERY_PARAMETER_NAME, IDENTIFIER_QUERY_PARAMETER_NAME]:
                raise tornado.web.HTTPError(
                    status_code=400,
                    log_message=f"Illegal query parameter '{query_param}'")
            for query_param_value in query_params[query_param]:
                query_param_value = query_param_value.decode("utf-8")
                if query_param == ORG_CODE_QUERY_PARAMETER_NAME \
                        and not query_param_value.startswith(f"{ORG_CODE_FHIR_IDENTIFIER}|"):
                    self._raise_invalid_query_param_error(ORG_CODE_QUERY_PARAMETER_NAME, ORG_CODE_FHIR_IDENTIFIER)
                if query_param == IDENTIFIER_QUERY_PARAMETER_NAME \
                        and not query_param_value.startswith(f"{SERVICE_ID_FHIR_IDENTIFIER}|") \
                        and not query_param_value.startswith(f"{PARTY_KEY_FHIR_IDENTIFIER}|"):
                    self._raise_invalid_identifier_query_param_error()

    @staticmethod
    def _raise_invalid_query_params_error():
        org_code = f'{ORG_CODE_QUERY_PARAMETER_NAME}={ORG_CODE_FHIR_IDENTIFIER}|value'
        party_key = f'{IDENTIFIER_QUERY_PARAMETER_NAME}={PARTY_KEY_FHIR_IDENTIFIER}|value'
        service_id = f'{IDENTIFIER_QUERY_PARAMETER_NAME}={SERVICE_ID_FHIR_IDENTIFIER}|value'

        raise tornado.web.HTTPError(
            status_code=400,
            log_message=f"Missing or invalid query parameters. "
                        f"Should one of following combinations: ["
                        f"'{org_code}&{service_id}&{party_key}'"
                        f"'{org_code}&{service_id}'"
                        f"'{org_code}&{party_key}'"
                        f"'{service_id}&{party_key}'"
                        "]")
