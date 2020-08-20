import json
from typing import Dict

from request.formatter_urls import FormatterUrls as Url


def get_json_format(combined_info: Dict, org_code: str, service_id: str):
    output = {"resourceType": "Endpoint"}
    output.update({"id": "f0f0e921-92ca-4a88-a550-2dbb36f703af"})
    output.update({"extension": build_extension_array(combined_info)})
    output.update({"identifier": build_identifier_array(combined_info, service_id)})
    output.update({"status": "active"})
    output.update({"connectionType": build_connection_type()})
    output.update({"managingOrganization": build_managing_organization(org_code)})
    output.update({"payloadType": build_payload_type()})
    output.update({"address": array_to_string(combined_info, "nhsMHSEndPoint")})

    return json.dumps(output, indent=2)


def build_extension_array(combined_info: Dict):
    return [{
        "url": Url.EXTENSION_URL,
        "extension": [
            build_extension("nhsMHSSyncReplyMode", "nhsMHSSyncReplyMode", combined_info),
            build_extension("nhsMHSRetryInterval", "nhsMHSRetryInterval", combined_info),
            build_int_extension("nhsMHSRetries", "nhsMHSRetries", combined_info),
            build_extension("nhsMHSPersistDuration", "nhsMHSPersistDuration", combined_info),
            build_extension("nhsMHSDuplicateElimination", "nhsMHSDuplicateElimination", combined_info),
            build_extension("nhsMHSAckRequested", "nhsMHSAckRequested", combined_info)
        ]
    }]


def build_extension(url: str, value: str, combined_info: Dict):
    return {
        "url": url,
        "valueString": array_to_string(combined_info, value)
    }


def build_int_extension(url: str, value: str, combined_info: Dict):
    return {
        "url": url,
        "valueInteger": int(array_to_string(combined_info, value) or 0)
    }


def build_identifier_array(combined_info: Dict, service_id: str):
    return [
        build_identifier(Url.NHS_ENDPOINT_SERVICE_ID_URL, service_id),
        build_identifier(Url.NHS_MHS_FQDN_URL, array_to_string(combined_info, "nhsMhsFQDN")),
        build_identifier(Url.NHS_MHS_PARTYKEY_URL, array_to_string(combined_info, "nhsMHSPartyKey")),
        build_identifier(Url.NHS_MHS_CPAID_URL, array_to_string(combined_info, "nhsMhsCPAId")),
        build_identifier(Url.NHS_SPINE_ASID_URL, array_to_string(combined_info, "uniqueIdentifier"))
    ]


def build_identifier(system: str, value: str):
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


def build_managing_organization(value: str):
    return {
        "identifier": build_identifier(Url.MANAGING_ORGANIZATION_URL, value)
    }


def build_payload_type():
    return [
        {
            "coding": [
                {
                    "system": Url.PAYLOAD_TYPE_URL,
                    "code": "any",
                    "display": "Any"
                }
            ]
        }
    ]


def build_address(value: str):
    return "https://{}/".format(value)


def array_to_string(combined_info: Dict, key: str):
    return str(combined_info.get(key)).strip("['']")
