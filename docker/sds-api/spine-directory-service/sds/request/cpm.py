import copy

from typing import List
from lookup.sds_exception import SDSException

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

    filtered_results = []
    filters = {
        "org_code": False,
        "service_id": False,
    }
    if "manufacturing_organization" in query_parts:
        filters["manufact_org"] = False
    if "party_key" in query_parts:
        filters["party_key"] = False
        
    for result in data["entry"]:
        if "resourceType" in result and result["resourceType"] == "Bundle":
            for index, res in enumerate(result["entry"]):
                if "resourceType" in res and res["resourceType"] == "QuestionnaireResponse":
                    for service in res["item"]:
                        if service["text"] == "Owner":
                            for answer in service["answer"]:
                                if answer["valueString"] == query_parts["org_code"]:
                                    filters["org_code"] = True
                        if service["text"] == "InteractionIds":
                            for answer in service["answer"]:
                                if answer["valueString"] == query_parts["interaction_id"]:
                                    filters["service_id"] = True
                                    break
                        if "manufacturing_organization" in query_parts and service["text"] == "ManufacturingOdsCode":
                            for answer in service["answer"]:
                                if answer["valueString"] == query_parts["manufacturing_organization"]:
                                    filters["manufact_org"] = True
                                    break
                        if "party_key" in query_parts and service["text"] == "PartyKey":
                            for answer in service["answer"]:
                                if answer["valueString"] == query_parts["party_key"]:
                                    filters["party_key"] = True
                                    break
        all_filters_true = all(value for value in filters.values())
        if all_filters_true:
            filtered_results.append(result["entry"])
        filters = {key: False for key in filters}
                    
    return filtered_results

def transform_device_to_SDS(data: List) -> List:
    ldap_data = []
    default_data_dict = dict(
        nhsAsClient = [],
        nhsAsSvcIA = [],
        nhsMhsManufacturerOrg = "",
        nhsMhsPartyKey = "",
        nhsIdCode = "",
        uniqueIdentifier = ""
    )

    for d in data:
        data_dict = copy.deepcopy(default_data_dict)
        for item in d:
            if "resource" in item:
                data_dict["uniqueIdentifier"] = process_device_resource(item["resource"])
            else:
                data_dict = process_questionnaire_response(item, data_dict)

        ldap_data.append(data_dict)

    return ldap_data


def process_device_resource(item):
    if "resourceType" in item and item["resourceType"] == "Device":
        if "identifier" in item:
            for identifier in item["identifier"]:
                if identifier.get("system") == "https://fhir.nhs.uk/Id/nhsSpineASID":
                    return identifier.get("value")
    return ""

def process_questionnaire_response(item, data_dict):
    if "resourceType" in item and item["resourceType"] == "QuestionnaireResponse":
        for service in item.get("item", []):
            if service["text"] == "InteractionIds":
                for answer in service["answer"]:
                    data_dict["nhsAsSvcIA"].append(answer["valueString"])
            elif service["text"] == "ManufacturingOdsCode":
                data_dict["nhsMhsManufacturerOrg"] = service["answer"][0].get("valueString", "")
            elif service["text"] == "PartyKey":
                data_dict["nhsMhsPartyKey"] = service["answer"][0].get("valueString", "")
            elif service["text"] == "Owner":
                data_dict["nhsAsClient"] = [service["answer"][0].get("valueString", "")]
                data_dict["nhsIdCode"] = service["answer"][0].get("valueString", "")
    return data_dict