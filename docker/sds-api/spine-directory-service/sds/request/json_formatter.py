import json
from typing import Dict

schemaLocation_url = "http://www.w3.org/2001/XMLSchema-instance"
attr_qname_url = "http://hl7.org/fhir file:///C:/Validation-Assets-R4/Schemas/fhir-all-xsd/fhir-all.xsd"
default_url = "http://hl7.org/fhir"
xsi_url = "http://www.w3.org/2001/XMLSchema-instance"
extension_url = "https://fhir.nhs.uk/R4/StructureDefinition/Extension-SDS-ReliabilityConfiguration"
nhs_endpoint_serviceId_url = "https://fhir.nhs.uk/Id/nhsEndpointServiceId"
nhs_mhs_fqdn_url = "https://fhir.nhs.uk/Id/nhsMhsFQDN"
nhs_mhs_endpoint_url = "https://fhir.nhs.uk/Id/nhsMhsEndPoint"
nhs_mhs_partykey_url = "https://fhir.nhs.uk/Id/nhsMhsPartyKey"
nhs_mhs_cpaid_url = "https://fhir.nhs.uk/Id/nhsMhsCPAId"
nhs_spine_asid_url = "https://fhir.nhs.uk/Id/nhsSpineASID"
connection_type_url = "http://terminology.hl7.org/CodeSystem/endpoint-connection-type"
managing_organization_url = "https://fhir.nhs.uk/Id/ods-organization-code"
payload_type_url = "http://terminology.hl7.org/CodeSystem/endpoint-payload-type"


def get_json_format(combined_info: Dict, org_code: str, service_id: str):
    output = {"resourceType": "Endpoint"}
    output.update({"id": "f0f0e921-92ca-4a88-a550-2dbb36f703af"})
    output.update({"extension": build_extension_array(combined_info)})
    output.update({"identifier": build_identifier_array(combined_info, service_id)})
    output.update({"status": "active"})
    output.update({"connectionType": "string"})
    output.update({"managingOrganization": build_managing_organization(managing_organization_url, org_code)})
    output.update({"payloadType": build_payload_type(payload_type_url, "any", "any")})
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
        build_identifier_dict(nhs_endpoint_serviceId_url, service_id),
        build_identifier_dict(nhs_mhs_fqdn_url, array_to_string(combined_info, "nhsMhsFQDN")),
        build_identifier_dict(nhs_mhs_endpoint_url, array_to_string(combined_info, "nhsMHSEndPoint")),
        build_identifier_dict(nhs_mhs_partykey_url, array_to_string(combined_info, "nhsMHSPartyKey")),
        build_identifier_dict(nhs_mhs_cpaid_url, array_to_string(combined_info, "nhsMhsCPAId")),
        build_identifier_dict(nhs_spine_asid_url, array_to_string(combined_info, "uniqueIdentifier"))
    ]


def build_identifier_dict(system: str, value: str):
    return {
        "system": system,
        "value": value
    }


def build_managing_organization(system_value: str, value_value: str):
    return {
        "system": system_value,
        "value": value_value
    }


def build_payload_type(system_value: str, code_value: str, display_value: str):
    return {
        "system": system_value,
        "code": code_value,
        "display": display_value
    }


def build_address(value: str):
    return "https://{}/".format(value)


def array_to_string(combined_info: Dict, key: str):
    return str(combined_info.get(key)).strip("['']")
