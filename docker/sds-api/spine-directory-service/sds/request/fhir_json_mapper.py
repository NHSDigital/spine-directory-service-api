from typing import Dict, List

from request.mapper_urls import MapperUrls as Url
from utilities import message_utilities


def build_bundle_resource(endpoints: List[Dict], base_url: str, full_url: str):
    return {
        "resourceType": "Bundle",
        "id": message_utilities.get_uuid(),
        "type": "searchset",
        "total": len(endpoints),
        "link": [
            {
                "relation": "self",
                "url": full_url
            }
        ],
        # TODO: endpoints dict can have multiple addresses inside and each must produce new resource
        "entry": list(map(lambda endpoint: _map_endpoint_to_entry(endpoint, base_url), endpoints))
    }


def _map_endpoint_to_entry(endpoint, base_url):
    return {
        "fullUrl": base_url + endpoint["id"],
        "resource": endpoint
    }


def build_endpoint_resource(ldap_attributes: Dict, org_code: str, service_id: str) -> List[Dict]:
    def build_endpoint(address):
        return {
            "resourceType": "Endpoint",
            "id": message_utilities.get_uuid(),
            "extension": build_extension_array(ldap_attributes),
            "identifier": build_identifier_array(ldap_attributes, service_id),
            "status": "active",
            "connectionType": build_connection_type(),
            "managingOrganization": build_managing_organization(org_code),
            "payloadType": build_payload_type(),
            "address": address
        }
    return [build_endpoint(address) for address in ldap_attributes['nhsMHSEndPoint']]


def build_extension_array(ldap_attributes: Dict):
    return [{
        "url": Url.EXTENSION_URL,
        "extension": [
            build_extension("nhsMHSSyncReplyMode", "nhsMHSSyncReplyMode", ldap_attributes),
            build_extension("nhsMHSRetryInterval", "nhsMHSRetryInterval", ldap_attributes),
            build_int_extension("nhsMHSRetries", "nhsMHSRetries", ldap_attributes),
            build_extension("nhsMHSPersistDuration", "nhsMHSPersistDuration", ldap_attributes),
            build_extension("nhsMHSDuplicateElimination", "nhsMHSDuplicateElimination", ldap_attributes),
            build_extension("nhsMHSAckRequested", "nhsMHSAckRequested", ldap_attributes)
        ]
    }]


def build_extension(url: str, value: str, ldap_attributes: Dict):
    return {
        "url": url,
        "valueString": array_to_string(ldap_attributes, value)
    }


def build_int_extension(url: str, value: str, ldap_attributes: Dict):

    return {
        "url": url,
        "valueInteger": string_to_int(array_to_string(ldap_attributes, value))
    }


def build_identifier_array(ldap_attributes: Dict, service_id: str):
    return [
        build_identifier(Url.NHS_ENDPOINT_SERVICE_ID_URL, service_id),
        build_identifier(Url.NHS_MHS_FQDN_URL, array_to_string(ldap_attributes, "nhsMhsFQDN")),
        build_identifier(Url.NHS_MHS_PARTYKEY_URL, array_to_string(ldap_attributes, "nhsMHSPartyKey")),
        build_identifier(Url.NHS_MHS_CPAID_URL, array_to_string(ldap_attributes, "nhsMhsCPAId")),
        build_identifier(Url.NHS_SPINE_MHS_URL, array_to_string(ldap_attributes, "uniqueIdentifier"))
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


def array_to_string(ldap_attributes: Dict, key: str):
    return str(ldap_attributes.get(key)).strip("['']")


def string_to_int(value: str):
    try:
        value_integer = int(value)
    except ValueError:
        value_integer = 0

    return value_integer
