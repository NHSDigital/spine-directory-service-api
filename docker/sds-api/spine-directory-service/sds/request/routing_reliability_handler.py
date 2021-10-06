import json
from typing import List, Set, Dict

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
from utilities import config

logger = log.IntegrationAdaptorsLogger(__name__)

FORWARD_RELIABLE_SERVICES = [
    'cc', 'ebs', 'ebsepr', 'ebsnpr', 'gp2gp', 'pat', 'itk', 'dis',
    'ed', 'op', 'caf', 'adm', 'ooh', 'am', 'mh', 'nd', 'dir']
FORWARD_RELIABLE_INTERACTIONS = [
    'COPC_IN000001UK01', 'PRSC_IN040000UK08', 'PRSC_IN080000UK07', 'PRPA_IN010000UK07', 'PRPA_IN020000UK06',
    'PRSC_IN050000UK06', 'PRSC_IN090000UK09', 'PRPA_IN030000UK08', 'PRSC_IN100000UK06', 'PRSC_IN070000UK08',
    'PRSC_IN140000UK06', 'RCMR_IN010000UK05', 'RCMR_IN030000UK06', 'PRSC_IN130000UK07', 'PRSC_IN110000UK08',
    'PRSC_IN060000UK06', 'PRSC_IN150000UK06', 'POLB_IN020006UK01', 'POLB_IN020005UK01', 'COMT_IN000004GB01',
    'MCCI_IN010000UK13'
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

        self._validate_query_params()

        org_code = self.get_optional_query_param(ORG_CODE_QUERY_PARAMETER_NAME, ORG_CODE_FHIR_IDENTIFIER)
        service_id = self.get_optional_query_param(IDENTIFIER_QUERY_PARAMETER_NAME, SERVICE_ID_FHIR_IDENTIFIER)
        party_key = self.get_optional_query_param(IDENTIFIER_QUERY_PARAMETER_NAME, PARTY_KEY_FHIR_IDENTIFIER)

        if (org_code and not service_id and not party_key) or (not org_code and (not service_id or not party_key)):
            self._raise_invalid_query_params_error()

        accept_type = get_valid_accept_type(self.request.headers)

        logger.info("Looking up routing and reliability information. {org_code}, {service_id}, {party_key}",
                    fparams={"org_code": org_code, "service_id": service_id, "party_key": party_key})
        ldap_results = await self.sds_client.get_mhs_details(org_code, service_id, party_key)
        logger.info("Obtained routing and reliability information. {ldap_results}",
                    fparams={"ldap_results": ldap_results})

        await self._handle_forward_reliable_results(ldap_results, org_code)

        base_url = f"{self.request.protocol}://{self.request.host}{self.request.path}/"
        full_url = unquote(self.request.full_url())

        endpoints = []
        for ldap_result in ldap_results:
            endpoints += build_endpoint_resources(ldap_result)

        bundle = build_bundle_resource(endpoints, base_url, full_url)

        self.write(json.dumps(bundle, indent=2, sort_keys=False))
        self.set_header(HttpHeaders.CONTENT_TYPE, accept_type)
        self.set_header(HttpHeaders.X_CORRELATION_ID, mdc.correlation_id.get())

    async def _handle_forward_reliable_results(self, ldap_results: List[dict], org_code: str = None):
        if not self._is_spine_core_ods_code(org_code):
            fr_service_ids = self._get_forward_reliable_service_ids(ldap_results)
            fr_addresses_map = await self._get_forward_reliable_addresses_map(fr_service_ids)
            self._replace_forward_reliable_endpoint(ldap_results, fr_addresses_map)

    def _get_forward_reliable_service_ids(self, ldap_results: List[dict]) -> Set[str]:
        service_ids = map(lambda single_result: single_result['nhsMhsSvcIA'], ldap_results)
        only_fr_service_ids = filter(lambda service_id: self._is_forward_reliable_service(service_id), service_ids)
        return set(only_fr_service_ids)

    async def _get_forward_reliable_addresses_map(self, fr_service_ids: Set[str]) -> Dict:
        result = {}
        for fr_service_id in fr_service_ids:
            fr_address = await self._get_forward_reliable_address(fr_service_id)
            result[fr_service_id] = fr_address
        return result

    @staticmethod
    def _is_spine_core_ods_code(org_code):
        spine_core_ods_code = config.get_config('SPINE_CORE_ODS_CODE')
        return spine_core_ods_code == org_code

    async def _get_forward_reliable_address(self, service_id: str) -> str:
        spine_core_ods_code = config.get_config('SPINE_CORE_ODS_CODE')
        logger.info("Looking up forward reliable routing and reliability information. {org_code}, {service_id}",
                    fparams={"org_code": spine_core_ods_code, "service_id": service_id})
        ldap_results = await self.sds_client.get_mhs_details(spine_core_ods_code, service_id)
        logger.info("Obtained forward reliable routing and reliability information. {ldap_results}",
                    fparams={"ldap_results": ldap_results})

        if len(ldap_results) != 1:
            raise ValueError(f"Expected 1 result for forward reliable routing and reliability but got {str(len(ldap_results))}")

        addresses = ldap_results[0]['nhsMHSEndPoint']

        if len(addresses) != 1:
            raise ValueError(f"Expected 1 address for forward reliable routing and reliability but got {str(len(addresses))}")

        return addresses[0]

    def _replace_forward_reliable_endpoint(self, ldap_results: List[dict], fr_addresses_map: Dict[str, str]):
        fr_ldap_result = (ldap_result for ldap_result in ldap_results if self._is_forward_reliable_service(ldap_result['nhsMhsSvcIA']))
        for single_fr_ldap_result in fr_ldap_result:
            single_fr_ldap_result['nhsMHSEndPoint'] = [fr_addresses_map[single_fr_ldap_result['nhsMhsSvcIA']]]

    @staticmethod
    def _is_forward_reliable_service(service_interaction: str):
        if not service_interaction:
            return False

        parts = service_interaction.split(':')

        if len(parts) < 2:
            raise RuntimeError(f"Invalid service interaction {service_interaction}")

        return parts[-2] in FORWARD_RELIABLE_SERVICES and parts[-1] in FORWARD_RELIABLE_INTERACTIONS

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
