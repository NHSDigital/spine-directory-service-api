import json
from typing import Dict

from request.formatter_urls import FormatterUrls as Url


def get_json_format(combined_info: Dict, org_code: str, service_id: str):
    output = {"resourceType": "Endpoint"}
    # what about this ID?
    output.update({"id": "f0f0e921-92ca-4a88-a550-2dbb36f703af"})
    output.update({"extension": build_extension_array(combined_info)})
    output.update({"identifier": build_identifier_array(combined_info, service_id)})
    output.update({"status": "active"})
    output.update({"connectionType": build_connection_type()})
    output.update({"managingOrganization": build_managing_organization(org_code)})
    output.update({"payloadType": build_payload_type()})
    output.update({"address": build_address(combined_info.get("nhsMhsFQDN"))})

    return json.dumps(output, indent=2)


def build_extension_array(combined_info: Dict):
    return [
        build_extension_dict("nhsMHSSyncReplyMode", "nhsMHSSyncReplyMode", combined_info),
        build_extension_dict("nhsMHSRetryInterval", "nhsMHSRetryInterval", combined_info),
        build_extension_dict("nhsMHSRetries", "nhsMHSRetries", combined_info),
        build_extension_dict("nhsMHSPersistDuration", "nhsMHSPersistDuration", combined_info),
        build_extension_dict("nhsMHSDuplicateElimination", "nhsMHSDuplicateElimination", combined_info),
        build_extension_dict("nhsMHSAckRequested", "nhsMHSAckRequested", combined_info)
    ]


def build_extension_dict(url: str, value: str, combined_info: Dict):
    return {
        "url": url,
        "valueString": array_to_string(combined_info, value)
    }


def build_identifier_array(combined_info: Dict, service_id: str):
    return [
        build_identifier_dict(Url.NHS_ENDPOINT_SERVICE_ID_URL, service_id),
        build_identifier_dict(Url.NHS_MHS_FQDN_URL, array_to_string(combined_info, "nhsMhsFQDN")),
        build_identifier_dict(Url.NHS_MHS_ENDPOINT_URL, array_to_string(combined_info, "nhsMHSEndPoint")),
        build_identifier_dict(Url.NHS_MHS_PARTYKEY_URL, array_to_string(combined_info, "nhsMHSPartyKey")),
        build_identifier_dict(Url.NHS_MHS_CPAID_URL, array_to_string(combined_info, "nhsMhsCPAId")),
        build_identifier_dict(Url.NHS_SPINE_ASID_URL, array_to_string(combined_info, "uniqueIdentifier"))
    ]


def build_identifier_dict(system: str, value: str):
    return {
        "system": system,
        "value": value
    }


def build_connection_type():
    return {
        "system": Url.CONNECTION_TYPE_URL,
        "code": "hl7-fhir-msg",
        "display": "HL7 FHIR Messaging"
    }


def build_managing_organization(value_value: str):
    return {
        "reference": Url.MANAGING_ORGANIZATION_URL,
        "display": value_value
    }


def build_payload_type():
    return [
        {
            "coding": [
                {
                    "system": Url.PAYLOAD_TYPE_URL,
                    "code": "any",
                    "display": "any"
                }
            ]
        }
    ]


def build_address(value: str):
    return "https://{}/".format(value)


def array_to_string(combined_info: Dict, key: str):
    return str(combined_info.get(key)).strip("['']")
