import json

from urllib.parse import unquote

import tornado

from request.base_handler import BaseHandler, USER_ROLE_ID_QUERY_PARAMETER_NAME, USER_ROLE_ID_FHIR_IDENTIFIER
from request.content_type_validator import get_valid_accept_type
from request.error_handler import ErrorHandler
from request.fhir_json_mapper import build_bundle_resource, build_practitioner_role_resource
from request.http_headers import HttpHeaders
from request.tracking_ids_headers_reader import read_tracking_id_headers
from utilities import timing, integration_adaptors_logger as log, mdc

logger = log.IntegrationAdaptorsLogger(__name__)


class PractitionerRoleHandler(BaseHandler, ErrorHandler):
    """A handler for requests to obtain practitioner role information."""

    @timing.time_request
    async def get(self):
        read_tracking_id_headers(self.request.headers)

        self._validate_query_params()

        accept_type = get_valid_accept_type(self.request.headers)

        user_role_id = self.get_required_query_param(USER_ROLE_ID_QUERY_PARAMETER_NAME, USER_ROLE_ID_FHIR_IDENTIFIER)

        logger.info("Looking up practitioner role information for {user_role_id}",
                    fparams={"user_role_id": user_role_id})
        ldap_result = await self.sds_client.get_practitioner_role_details(user_role_id)
        logger.info("Obtained practitioner role information. {ldap_result}",
                    fparams={"ldap_result": ldap_result})

        base_url = f"{self.request.protocol}://{self.request.host}{self.request.path}/"
        full_url = unquote(self.request.full_url())

        practitioner_roles = [build_practitioner_role_resource(ldap_attributes) for ldap_attributes in ldap_result]

        bundle = build_bundle_resource(practitioner_roles, base_url, full_url)

        self.write(json.dumps(bundle, indent=2, sort_keys=False))
        self.set_header(HttpHeaders.CONTENT_TYPE, accept_type)
        self.set_header(HttpHeaders.X_CORRELATION_ID, mdc.correlation_id.get())

    def _validate_query_params(self):
        query_params = self.request.arguments
        for query_param in query_params.keys():
            if query_param not in [USER_ROLE_ID_QUERY_PARAMETER_NAME]:
                raise tornado.web.HTTPError(
                    status_code=400,
                    log_message=f"Illegal query parameter '{query_param}' should be: '{USER_ROLE_ID_QUERY_PARAMETER_NAME}'")
            for query_param_value in query_params[query_param]:
                query_param_value = query_param_value.decode("utf-8")
                if query_param == USER_ROLE_ID_QUERY_PARAMETER_NAME \
                    and not query_param_value.startswith(f"{USER_ROLE_ID_FHIR_IDENTIFIER}|"):
                    self._raise_invalid_query_param_error(USER_ROLE_ID_QUERY_PARAMETER_NAME, USER_ROLE_ID_FHIR_IDENTIFIER)
                if query_param == USER_ROLE_ID_QUERY_PARAMETER_NAME \
                    and not query_param_value.is_digit():
                    self._raise_invalid_query_param_value_error(USER_ROLE_ID_QUERY_PARAMETER_NAME, USER_ROLE_ID_FHIR_IDENTIFIER, "a digit")

