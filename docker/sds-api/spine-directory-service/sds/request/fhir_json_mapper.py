from typing import Dict, List, Optional

from request.mapper_urls import MapperUrls as Url
from utilities import message_utilities


def build_bundle_resource(resources: List[Dict], base_url: str, full_url: str):
    return {
        "resourceType": "Bundle",
        "id": message_utilities.get_uuid(),
        "type": "searchset",
        "total": len(resources),
        "link": [
            {
                "relation": "self",
                "url": full_url
            }
        ],
        "entry": list(map(lambda resource: _map_resource_to_bundle_entry(resource, base_url), resources))
    }


def _map_resource_to_bundle_entry(resource, base_url):
    return {
        "fullUrl": base_url + resource["id"],
        "resource": resource,
        "search": {
            "mode": "match"
        }
    }


def build_endpoint_resources(ldap_attributes: Dict) -> List[Dict]:
    def build_endpoint(address):
        result = {
            "resourceType": "Endpoint",
            "id": message_utilities.get_uuid(),
            "status": "active",
            "connectionType": build_connection_type(),
            "payloadType": _build_payload_type(),
            "address": address
        }

        managing_organization = _build_managing_organization(ldap_attributes.get("nhsIDCode"))
        if managing_organization:
            result["managingOrganization"] = managing_organization

        identifiers = _build_identifier_array(ldap_attributes)
        identifiers = list(filter(lambda item: item, identifiers))
        if identifiers:
            result["identifier"] = identifiers

        extensions = _build_extension_array(ldap_attributes)
        extensions = list(filter(lambda item: item, extensions))
        if extensions:
            result["extension"] = [{
                "url": Url.EXTENSION_URL,
                "extension": extensions
            }]

        return result
    return [build_endpoint(address) for address in ldap_attributes['nhsMHSEndPoint']]


def build_device_resource(ldap_attributes: Dict) -> Dict:
    device = {
        "resourceType": "Device",
        "id": message_utilities.get_uuid()
    }
    managing_organization = ldap_attributes.get('nhsIdCode')
    if managing_organization:
        device["extension"] = [
            {
                "url": Url.MANAGING_ORGANIZATION_EXTENSION_URL,
                "valueReference": {
                    "identifier": {
                        "system": Url.MANAGING_ORGANIZATION_URL,
                        "value": managing_organization
                    }
                }
            }
        ]

    identifiers = []
    unique_identifier = (ldap_attributes.get('uniqueIdentifier') or [None])[0]
    if unique_identifier:
        identifiers.append(build_identifier(Url.NHS_SPINE_ASID, unique_identifier))
    party_key = ldap_attributes.get('nhsMhsPartyKey')
    if party_key:
        identifiers.append(build_identifier(Url.NHS_MHS_PARTYKEY_URL, party_key))
    #TODO: should this be a coma separated list or something else?
    service_id = ",".join(ldap_attributes.get('nhsAsSvcIA'))
    if service_id:
        identifiers.append(build_identifier(Url.NHS_ENDPOINT_SERVICE_ID_URL, service_id))
    if identifiers:
        device['identifier'] = identifiers

    client_id = (ldap_attributes.get('nhsAsClient') or [None])[0]
    if client_id:
        device["owner"] = {
            "identifier": {
                "system": Url.MANAGING_ORGANIZATION_URL,
                "value": client_id
            }
        }

    return device


def _build_identifier_array(ldap_attributes: Dict):
    return [
        build_identifier(Url.NHS_ENDPOINT_SERVICE_ID_URL, ldap_attributes.get("nhsMhsSvcIA")),
        build_identifier(Url.NHS_MHS_FQDN_URL, ldap_attributes.get("nhsMhsFQDN")),
        build_identifier(Url.NHS_MHS_PARTYKEY_URL, ldap_attributes.get("nhsMHSPartyKey")),
        build_identifier(Url.NHS_MHS_CPAID_URL, ldap_attributes.get("nhsMhsCPAId")),
        build_identifier(Url.NHS_SPINE_MHS_URL, (ldap_attributes.get("uniqueIdentifier") or [None])[0])
    ]


def _build_extension_array(ldap_attributes: Dict):
    return [
        _build_string_extension("nhsMHSSyncReplyMode", ldap_attributes.get("nhsMHSSyncReplyMode")),
        _build_string_extension("nhsMHSRetryInterval", ldap_attributes.get("nhsMHSRetryInterval")),
        _build_int_extension("nhsMHSRetries", ldap_attributes.get("nhsMHSRetries")),
        _build_string_extension("nhsMHSPersistDuration", ldap_attributes.get("nhsMHSPersistDuration")),
        _build_string_extension("nhsMHSDuplicateElimination", ldap_attributes.get("nhsMHSDuplicateElimination")),
        _build_string_extension("nhsMHSAckRequested", ldap_attributes.get("nhsMHSAckRequested"))
    ]


def _build_string_extension(url: str, value: str):
    return {
        "url": url,
        "valueString": value
    } if value else None


def _build_int_extension(url: str, value: str):
    return {
        "url": url,
        "valueInteger": int(value)
    } if value else None


def build_identifier(system: str, value: str):
    return {
        "system": system,
        "value": value
    } if value else None


def build_connection_type():
    return {
        "system": Url.CONNECTION_TYPE_URL,
        "code": "hl7-fhir-msg",
        "display": "HL7 FHIR Messaging"
    }


def _build_managing_organization(value: str):
    return {
        "identifier": build_identifier(Url.MANAGING_ORGANIZATION_URL, value)
    } if value else None


def _build_payload_type():
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


def _build_address(value: str):
    return "https://{}/".format(value)
