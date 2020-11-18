from typing import Optional

import tornado.web

from request.tracking_ids_headers_reader import read_tracking_id_headers
from lookup import routing_reliability


ORG_CODE_QUERY_PARAMETER_NAME = "organization"
IDENTIFIER_QUERY_PARAMETER_NAME = "identifier"

ORG_CODE_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/ods-organization-code"
SERVICE_ID_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/nhsEndpointServiceId"
PARTY_KEY_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/nhsMhsPartyKey"


class BaseHandler(tornado.web.RequestHandler):
    """A base handler for spine route lookup"""

    def initialize(self, routing: routing_reliability.RoutingAndReliability) -> None:
        """Initialise this request handler with the provided configuration values.

        :param routing: The routing and reliability component to use to look up values in SDS.
        """
        self.routing = routing
        read_tracking_id_headers(self.request.headers)

    def prepare(self):
        if self.request.method != "GET":
            raise tornado.web.HTTPError(
                status_code=405,
                reason="Method not allowed.")

    @staticmethod
    def _build_missing_or_invalid_query_param_error(query_param_name: str, fhir_identifier: str):
        return tornado.web.HTTPError(
            status_code=400,
            reason=f"Missing or invalid '{query_param_name}' query parameter. Should be '{query_param_name}={fhir_identifier}|value'")

    def _get_required_query_param(self, query_param_name: str, fhir_identifier: str) -> str:
        value = self.get_query_argument(query_param_name)
        parts = value.split("|")
        if len(parts) != 2 or parts[0] != fhir_identifier or not parts[1]:
            raise self._build_missing_or_invalid_query_param_error(query_param_name, fhir_identifier)
        return value[value.index("|") + 1:]

    def _get_optional_query_param(self, query_param_name: str, fhir_identifier: str) -> Optional[str]:
        values = list(filter(
            lambda value: "|" in value and value.split("|")[0] == fhir_identifier and value.split("|")[1],
            self.get_query_arguments(query_param_name)))

        last_value = values and values[-1]
        result_value = (last_value and last_value[last_value.index("|") + 1:]) or None
        return result_value
