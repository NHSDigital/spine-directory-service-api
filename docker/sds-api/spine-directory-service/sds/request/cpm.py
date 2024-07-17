import asyncio
import os
import copy
import tornado
import requests
from requests.exceptions import Timeout

from typing import List, Dict
from lookup.sds_exception import SDSException
from request.base_handler import ORG_CODE_QUERY_PARAMETER_NAME, ORG_CODE_FHIR_IDENTIFIER, \
    IDENTIFIER_QUERY_PARAMETER_NAME, SERVICE_ID_FHIR_IDENTIFIER, PARTY_KEY_FHIR_IDENTIFIER
from request.cpm_config import DEVICE_FILTER_MAP, ENDPOINT_FILTER_MAP, DEVICE_DATA_MAP, ENDPOINT_DATA_MAP, DEFAULT_ENDPOINT_DICT, DEFAULT_DEVICE_DICT
from utilities.constants import INTERACTION_MAPPINGS, RELIABLE_SERVICES
from utilities import config
from utilities import integration_adaptors_logger as log

logger = log.IntegrationAdaptorsLogger(__name__)


async def get_device_from_cpm(tracking_id_headers: dict, **query_parts) -> List:
    try:
        client_id = os.environ["CPM_CLIENT_KEY"]
        apigee_url = f"{os.environ['APIGEE_URL']}/{os.environ['CPM_PATH_URL']}"
    except KeyError as e:
        raise KeyError(f"Environment variable is required {e}")
    cpm_client = DeviceClient(client_id=client_id, apigee_url=apigee_url, endpoint="product", query_params=query_parts)
    data = await cpm_client.get_cpm(extra_headers=tracking_id_headers)

    return process_cpm_device_request(data=data)


async def get_endpoint_from_cpm(tracking_id_headers: dict, **query_parts) -> List:
    try:
        client_id = os.environ["CPM_CLIENT_KEY"]
        apigee_url = f"{os.environ['APIGEE_URL']}/{os.environ['CPM_PATH_URL']}"
    except KeyError as e:
        raise KeyError(f"Environment variable is required {e}")
    cpm_client = EndpointClient(client_id=client_id, apigee_url=apigee_url, endpoint="endpoint", query_params=query_parts)
    data = await cpm_client.get_cpm(extra_headers=tracking_id_headers)

    return process_cpm_endpoint_request(data=data, query_parts=query_parts)

def process_cpm_endpoint_request(data: dict):
    endpoints = EndpointCpm(data=data)
    ldap_converted = endpoints.transform_to_ldap(endpoints)
    return endpoints.set_mhs_endpoint(ldap_converted)

def process_cpm_device_request(data: dict):
    devices = BaseCpm(data=data)
    return devices.transform_to_ldap(devices)

def make_get_request(call_name: str, url, headers=None, params=None):
    res = requests.get(url, headers=headers, params=params)
    handle_error(res, call_name)
    return res

def handle_error(response, call_name):
    if response.status_code != 200:
        detail = f"Request to {call_name} failed with status code: {response.status_code} and message: {response.text}"
        logger.info(detail)
        raise SDSException(detail)

class CpmClient:
    def __init__(self, client_id: str, apigee_url: str,  endpoint: str, query_params: dict) -> None:
        self._client_id = client_id
        self._apigee_url = apigee_url
        self._endpoint = endpoint
        self._params = self._set_params(query_params)
        
    async def get_cpm(self, extra_headers: dict):
        logger.info("Contacting CPM")
        url = f"https://{self._apigee_url}"
        search_endpoint = f"Device"
        headers = {
            'version': '1',
            'Authorization': 'letmein',
            'Content-Type': 'application/json',
            'apiKey': self._client_id,
            **extra_headers
        }
        logger.info("Requesting data from... {url}/{endpoint}", fparams={"url": url, "endpoint": search_endpoint,  "query_params": self._params})
        res = make_get_request(call_name="SDS get_cpm", url=f"{url}/{search_endpoint}", headers=headers, params=self._params)
        return self._get_response(res=res)

    def _set_params(self, query_params: Dict[str, str]) -> Dict[str, str]:
        params = {key: value for key, value in query_params.items() if value is not None}
        params['device_type'] = self._endpoint
        params['use_mock'] = "true"
        return params

    def _get_response(self, res):
        return res.json()

class DeviceClient(CpmClient):
    def __init__(self, client_id: str, apigee_url: str,  endpoint: str, query_params: dict) -> None:
        self.validate_filters(query_params)
        super().__init__(client_id, apigee_url, endpoint, query_params)

    def validate_filters(self, query_params):
        if "org_code" not in query_params or "interaction_id" not in query_params or not query_params["org_code"] or not query_params["interaction_id"]:
            raise SDSException("org_code and interaction_id must be provided")

class EndpointClient(CpmClient):
    def __init__(self, client_id: str, apigee_url: str,  endpoint: str, query_params: dict) -> None:
        self.validate_filters(query_params)
        super().__init__(client_id, apigee_url, endpoint, query_params)

    def validate_filters(self, query_params):
        non_empty_count = sum(1 for value in query_params.values() if value and value != 0)
        if non_empty_count < 2:
            self._raise_invalid_query_params_error()
    
    def _raise_invalid_query_params_error(self):
        org_code = f'{ORG_CODE_QUERY_PARAMETER_NAME}={ORG_CODE_FHIR_IDENTIFIER}|value'
        party_key = f'{IDENTIFIER_QUERY_PARAMETER_NAME}={PARTY_KEY_FHIR_IDENTIFIER}|value'
        service_id = f'{IDENTIFIER_QUERY_PARAMETER_NAME}={SERVICE_ID_FHIR_IDENTIFIER}|value'
        log_message=f"Missing or invalid query parameters. Should one of following combinations: ['{org_code}&{service_id}&{party_key}','{org_code}&{service_id}','{org_code}&{party_key}','{service_id}&{party_key}']"
        raise SDSException(log_message)

class BaseCpm:
    FILTER_MAP = {}
    DATA_MAP = {}
    DEFAULT_DICT = {}

    def __init__(self, data):
        self.data = data

    @staticmethod
    def process_questionnaire_response(self, item, data_dict, ldap_data_mapping):
        for service in item.get("item", []):
            if service["text"] in ldap_data_mapping:
                for answer in service["answer"]:
                    key = ldap_data_mapping[service["text"]]
                    value = answer.get("valueInteger", answer.get("valueString"))
                    data_dict = self.set_data(data_dict, key, value)

        return data_dict

    @staticmethod
    def set_data(data_dict, key, value):
        if isinstance(data_dict[key], list):
            data_dict[key].append(value)
        else:
            data_dict[key] = value

        return data_dict

    def transform_to_ldap(self, data: List) -> List:
        ldap_data = []

        for d in data:
            data_dict = copy.deepcopy(self.DEFAULT_DICT)
            for item in d:
                if item.get("resourceType") == "QuestionnaireResponse":
                    data_dict = self.process_questionnaire_response(self, item, data_dict, self.DATA_MAP)

            ldap_data.append(data_dict)

        return ldap_data


class EndpointCpm(BaseCpm):
    FILTER_MAP = ENDPOINT_FILTER_MAP
    DATA_MAP = ENDPOINT_DATA_MAP
    DEFAULT_DICT = DEFAULT_ENDPOINT_DICT

    def __init__(self, data):
        super().__init__(data)

    def set_mhs_endpoint(self, ldap_results):
        for key, ldap_result in enumerate(ldap_results):
            service, interaction = self._extract_service_and_interaction(ldap_result['nhsMhsSvcIA'])
            if service in RELIABLE_SERVICES:
                address: Optional[str] = None
                for core_spine_interaction, interactions in INTERACTION_MAPPINGS.items():
                    if interaction in interactions:
                        address = self._get_address(core_spine_interaction)
                        break

                if address:
                    ldap_results[key]['nhsMHSEndPoint'] = address

        return ldap_results

    @staticmethod
    def _extract_service_and_interaction(service_interaction: str):
        if not service_interaction:
            return False

        parts = service_interaction.split(':')

        if len(parts) < 2:
            raise RuntimeError(f"Invalid service interaction: {service_interaction}")

        interaction_part = parts[-1]
        service_part = parts[-2]

        return service_part, interaction_part

    def _get_address(self, service_id: str) -> str:
        spine_core_ods_code = config.get_config('SPINE_CORE_ODS_CODE')
        logger.info("Looking up forward reliable/express routing and reliability information. {org_code}, {service_id}",
                    fparams={"org_code": spine_core_ods_code, "service_id": service_id})
        query_params = {
            "org_code": spine_core_ods_code,
            "interaction_id": service_id
        }
        address_endpoint = EndpointCpm(data=self.data, query_parts=query_params)
        filtered_address_endpoint = address_endpoint.filter_cpm_response()
        ldap_address = address_endpoint.transform_to_ldap(filtered_address_endpoint)

        address = []
        try:
            if len(ldap_address) == 1:
                address = ldap_address[0] if len(ldap_address) == 1 else self._raise_value_error("result", ldap_address)
                return address.get('nhsMHSEndPoint') if len(address['nhsMHSEndPoint']) == 1 else self._raise_value_error("address", address)
        except IndexError:
            self._raise_index_error("result", ldap_address)

    def _raise_value_error(self, message: str, address: List = []):
        raise ValueError(f"Expected 1 {message} for forward reliable/express routing and reliability but got {str(len(address))}")

    def _raise_index_error(self, message: str, address: List = []):
        raise IndexError(f"Expected 1 {message} for forward reliable/express routing and reliability but got {str(len(address))}")
