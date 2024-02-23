import copy
import tornado

from typing import List
from lookup.sds_exception import SDSException
from request.base_handler import ORG_CODE_QUERY_PARAMETER_NAME, ORG_CODE_FHIR_IDENTIFIER, \
    IDENTIFIER_QUERY_PARAMETER_NAME, SERVICE_ID_FHIR_IDENTIFIER, PARTY_KEY_FHIR_IDENTIFIER
from request.cpm_config import DEVICE_FILTER_MAP, ENDPOINT_FILTER_MAP, DEVICE_DATA_MAP, ENDPOINT_DATA_MAP, DEFAULT_ENDPOINT_DICT, DEFAULT_DEVICE_DICT

#TODO: Remove when connection to CPM is made.
import os
import json
RETURNED_DEVICES_JSON = "returned_devices.json"
RETURNED_ENDPOINTS_JSON = "returned_endpoints.json"


async def get_device_from_cpm(org_code: str, interaction_id: str, manufacturing_organization: str = None, party_key: str = None) -> List:
    query_parts = locals()
    data = request_cpm("device")
    return process_cpm_device_request(data=data, query_parts=query_parts)


async def get_endpoint_from_cpm(ods_code: str, interaction_id: str = None, party_key: str = None) -> List:
    return [
        {
            "ods-code": ods_code,
            "interaction_id": interaction_id,
            "party_key": party_key
        }
    ]

def request_cpm(endpoint):
    # TODO: temporary functionality, will just load the mock for now but eventually it will return from CPM
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("tests", "test_data", "cpm", RETURNED_ENDPOINTS_JSON))
    if endpoint.lower().capitalize() == "Device":
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("tests", "test_data", "cpm", RETURNED_DEVICES_JSON))
    with open(dir_path, 'r') as f:
        return json.load(f)

def process_cpm_endpoint_request(data: dict, query_parts: dict):
    endpoints = EndpointCpm(data=data, query_parts=query_parts)
    filtered_endpoints = endpoints.filter_cpm_response()
    return endpoints.transform_to_ldap(filtered_endpoints)

def process_cpm_device_request(data: dict, query_parts: dict):
    devices = DeviceCpm(data=data, query_parts=query_parts)
    filtered_devices = devices.filter_cpm_response()
    return devices.transform_to_ldap(filtered_devices)

class BaseCpm:
    FILTER_MAP = {}
    DATA_MAP = {}
    DEFAULT_DICT = {}
    
    def __init__(self, data, query_parts):
        self.data = data
        self.query_parts = query_parts

    def filter_cpm_response(self):
        filtered_results = []
        filters = {key: False for key, value in self.query_parts.items() if value is not None}
        
        for result in self.data["entry"]:
            for index, res in enumerate(result["entry"]) if result.get("resourceType") == "Bundle" else []:
                for service in res["item"] if res.get("resourceType") == "QuestionnaireResponse" else []:
                    filters = self._check_each_item(self, filters, service)
                
            all_filters_true = all(filters.values())
            if all_filters_true:
                filtered_results.append(result["entry"])
            filters = {key: False for key in filters}
        
        return filtered_results
    
    @staticmethod
    def _check_each_item(self, filters, service):
        for key, value in self.query_parts.items():
            if service["text"] == self.FILTER_MAP[key]:
                filters[key] = self._check_match(self, service["answer"], value)
        return filters
    
    @staticmethod
    def _check_match(self, answers, match):
        return any(answer["valueString"] == match for answer in answers)
    
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
    
    def __init__(self, data, query_parts):
        self.validate_filters(query_parts)
        super().__init__(data, query_parts)
    
    def validate_filters(self, query_parts):
        non_empty_count = sum(1 for value in query_parts.values() if value and value != 0)
        if non_empty_count < 2:
            self._raise_invalid_query_params_error()
    
    def _raise_invalid_query_params_error(self):
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


class DeviceCpm(BaseCpm):
    FILTER_MAP = DEVICE_FILTER_MAP
    DATA_MAP = DEVICE_DATA_MAP
    DEFAULT_DICT = DEFAULT_DEVICE_DICT
    
    def __init__(self, data, query_parts):
        self.validate_filters(query_parts)
        super().__init__(data, query_parts)
    
    def validate_filters(self, query_parts):
        if "org_code" not in query_parts or "interaction_id" not in query_parts or not query_parts["org_code"] or not query_parts["interaction_id"]:
            raise SDSException("org_code and interaction_id must be provided")
