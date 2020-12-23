from typing import Optional, Set

import tornado.web

from lookup.sds_client import SDSClient
from utilities import mdc, message_utilities

ORG_CODE_QUERY_PARAMETER_NAME = "organization"
IDENTIFIER_QUERY_PARAMETER_NAME = "identifier"
MANAGING_ORGANIZATION_QUERY_PARAMETER_NAME = "managing-organization"

ORG_CODE_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/ods-organization-code"
SERVICE_ID_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/nhsEndpointServiceId"
PARTY_KEY_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/nhsMhsPartyKey"
MANAGING_ORGANIZATION_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/ods-organization-code"


class BaseHandler(tornado.web.RequestHandler):
    """A base handler for spine route lookup"""

    def initialize(self, sds_client: SDSClient) -> None:
        """Initialise this request handler with the provided configuration values.

        :param sds_client: The sds client component to use to look up values in SDS.
        """
        mdc.trace_id.set(message_utilities.get_uuid())
        self.sds_client = sds_client

    def prepare(self):
        if self.request.method != "GET":
            raise tornado.web.HTTPError(
                status_code=405,
                reason="Method not allowed.")

    def get_required_query_param(self, query_param_name: str, fhir_identifier: str) -> Optional[str]:
        value = self.get_optional_query_param(query_param_name, fhir_identifier)
        if not value:
            raise tornado.web.HTTPError(
                status_code=400,
                reason=f"Missing or invalid '{query_param_name}' query parameter. Should be '{query_param_name}={fhir_identifier}|value'")
        return value

    def get_optional_query_param(self, query_param_name: str, fhir_identifier: str) -> Optional[str]:
        values = list(filter(
            lambda value: "|" in value and value.split("|")[0] == fhir_identifier and value[value.index("|") + 1:].strip(),
            self.get_query_arguments(query_param_name)))

        last_value = values and values[-1]
        result_value = (last_value and last_value[last_value.index("|") + 1:]) or None
        return result_value

    def validate_optional_query_parameters(self, query_param_name: str, valid_fhir_identifiers: Set[str]):
        all_values = self.get_query_arguments(query_param_name)

        values_without_pipe = list(map(lambda value: f"{query_param_name}={value}", filter(lambda value: "|" not in value, all_values)))
        if values_without_pipe:
            raise tornado.web.HTTPError(
                status_code=400,
                reason=f"Unsupported query parameter(s): {', '.join(values_without_pipe)}")

        invalid_fhir_identifier = [x for x in all_values if x.split("|")[0] not in valid_fhir_identifiers]
        invalid_fhir_identifier = list(map(lambda value: f"{query_param_name}={value}", invalid_fhir_identifier))
        if invalid_fhir_identifier:
            raise tornado.web.HTTPError(
                status_code=400,
                reason=f"Unsupported query parameter(s): {', '.join(invalid_fhir_identifier)}")
