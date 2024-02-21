import copy
import tornado

from typing import List
from lookup.sds_exception import SDSException
from request.base_handler import ORG_CODE_QUERY_PARAMETER_NAME, ORG_CODE_FHIR_IDENTIFIER, \
    IDENTIFIER_QUERY_PARAMETER_NAME, SERVICE_ID_FHIR_IDENTIFIER, PARTY_KEY_FHIR_IDENTIFIER
from request.cpm_config import DEVICE_FILTER_MAP, ENDPOINT_FILTER_MAP, DEVICE_DATA_MAP, ENDPOINT_DATA_MAP, DEFAULT_ENDPOINT_DICT, DEFAULT_DEVICE_DICT


async def get_device_from_cpm(ods_code: str, interaction_id: str, manufacturing_organization: str = None, party_key: str = None) -> List:
    return [
        {
            "ods-code": ods_code,
            "interaction_id": interaction_id,
            "manufacturing_organisation": manufacturing_organization,
            "party_key": party_key
        }
    ]


async def get_endpoint_from_cpm(ods_code: str, interaction_id: str = None, party_key: str = None) -> List:
    return [
        {
            "ods-code": ods_code,
            "interaction_id": interaction_id,
            "party_key": party_key
        }
    ]


def filter_cpm_devices_response(data: dict, query_parts: dict):
    if "org_code" not in query_parts or "interaction_id" not in query_parts or not query_parts["org_code"] or not query_parts["interaction_id"]:
            raise SDSException("org_code and interaction_id must be provided")

    return filter_cpm_response(data, query_parts, DEVICE_FILTER_MAP)


def filter_cpm_endpoints_response(data: dict, query_parts: dict):
    non_empty_count = sum(1 for value in query_parts.values() if value and value != 0)
    if non_empty_count < 2:
        _raise_invalid_query_params_error()

    return filter_cpm_response(data, query_parts, ENDPOINT_FILTER_MAP)


def filter_cpm_response(data: dict, query_parts: dict, query_mapping: dict):
    filtered_results = []
    filters = {key: False for key in query_parts}
    
    for result in data["entry"]:
        if "resourceType" in result and result["resourceType"] == "Bundle":
            for index, res in enumerate(result["entry"]):
                if "resourceType" in res and res["resourceType"] == "QuestionnaireResponse":
                    for service in res["item"]:
                        for key, value in query_parts.items():
                            if service["text"] == query_mapping[key]:
                                for answer in service["answer"]:
                                    if answer["valueString"] == value:
                                        filters[key] = True                   
        all_filters_true = all(value for value in filters.values())
        if all_filters_true:
            filtered_results.append(result["entry"])
        filters = {key: False for key in filters}
    
    return filtered_results


def transform_endpoint_to_SDS(data: List) -> List:
    ldap_data = []

    for d in data:
        data_dict = copy.deepcopy(DEFAULT_ENDPOINT_DICT)
        for item in d:
            data_dict = process_questionnaire_response(item, data_dict, ENDPOINT_DATA_MAP)

        ldap_data.append(data_dict)

    return ldap_data


def transform_device_to_SDS(data: List) -> List:
    ldap_data = []
    
    for d in data:
        data_dict = copy.deepcopy(DEFAULT_DEVICE_DICT)
        for item in d:
            if "resource" in item:
                data_dict["uniqueIdentifier"] = process_device_response(item["resource"])
            else:
                data_dict = process_questionnaire_response(item, data_dict, DEVICE_DATA_MAP)

        ldap_data.append(data_dict)

    return ldap_data


def process_questionnaire_response(item, data_dict, ldap_data_mapping):
    if "resourceType" in item and item["resourceType"] == "QuestionnaireResponse":      
        for service in item.get("item", []):
            if service["text"] in ldap_data_mapping:
                for answer in service["answer"]:
                    key = ldap_data_mapping[service["text"]]
                    value = answer.get("valueInteger", answer.get("valueString"))
                    if not isinstance(key, list):
                        data_dict = get_data(data_dict, key, value)
                    else:
                        for secondary_key in key:
                            data_dict = get_data(data_dict, secondary_key, value)
                        
    return data_dict


def process_device_response(item):
    if "resourceType" in item and item["resourceType"] == "Device":
        if "identifier" in item:
            for identifier in item["identifier"]:
                if identifier.get("system") == "https://fhir.nhs.uk/Id/nhsSpineASID":
                    return identifier.get("value")
    return ""


def get_data(data_dict, key, value):
    if isinstance(data_dict[key], list):
        data_dict[key].append(value)
    elif isinstance(data_dict[key], int):
        data_dict[key] = value
    else:
        data_dict[key] = value
    
    return data_dict


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
