from typing import Dict

from lxml import etree

from request.formatter_urls import FormatterUrls as Url


def get_xml_format(combined_info: Dict, org_code: str, service_id: str):
    root = build_root_element()
    root.append(etree.Element("id", value="f0f0e921-92ca-4a88-a550-2dbb36f703af"))
    root.append(build_extension_node(combined_info))
    root.append(build_identifier_node(Url.NHS_ENDPOINT_SERVICE_ID_URL, service_id))
    root.append(build_identifier_node(Url.NHS_MHS_FQDN_URL, combined_info.get("nhsMhsFQDN")))
    root.append(build_identifier_node(Url.NHS_MHS_PARTYKEY_URL, combined_info.get("nhsMHSPartyKey")))
    root.append(build_identifier_node(Url.NHS_MHS_CPAID_URL, combined_info.get("nhsMhsCPAId")))
    root.append(build_identifier_node(Url.NHS_SPINE_ASID_URL, array_to_string(combined_info, "uniqueIdentifier")))
    root.append(etree.Element("status", value="active"))
    root.append(build_connection_type(Url.CONNECTION_TYPE_URL, "hl7-fhir-msg", "HL7 FHIR Messaging"))
    root.append(build_managing_organization(Url.MANAGING_ORGANIZATION_URL, org_code))
    root.append(build_payload_type(Url.PAYLOAD_TYPE_URL, "any", "Any"))
    root.append(etree.Element("address", value=array_to_string(combined_info, "nhsMHSEndPoint")))

    return etree.tostring(root, pretty_print=True).decode()


def build_root_element():
    return etree.Element("Endpoint", xmlns="http://hl7.org/fhir")


def build_extension_node(combined_info: Dict):
    ext = etree.Element("extension", url=Url.EXTENSION_URL)
    ext.append(build_string_extension("nhsMHSSyncReplyMode", array_to_string(combined_info, "nhsMHSSyncReplyMode")))
    ext.append(build_string_extension("nhsMHSRetryInterval", array_to_string(combined_info, "nhsMHSRetryInterval")))
    ext.append(build_integer_extension("nhsMHSRetries", array_to_string(combined_info, "nhsMHSRetries")))
    ext.append(build_string_extension("nhsMHSPersistDuration", array_to_string(combined_info, "nhsMHSPersistDuration")))
    ext.append(build_string_extension("nhsMHSDuplicateElimination", combined_info.get("nhsMHSDuplicateElimination")))
    ext.append(build_string_extension("nhsMHSAckRequested", combined_info.get("nhsMHSAckRequested")))

    return ext


def build_string_extension(url: str, value: str):
    extension_sub = etree.Element("extension", url=url)
    extension_sub.append(etree.SubElement(extension_sub, "valueString", value=value))
    return extension_sub


def build_integer_extension(url: str, value: str):
    extension_sub = etree.Element("extension", url=url)
    extension_sub.append(etree.SubElement(extension_sub, "valueInteger", value=value))
    return extension_sub


def build_identifier_node(system_value: str, value_value: str):
    identifier_node = etree.Element("identifier")
    identifier_node.append(etree.SubElement(identifier_node, "system", value=system_value))
    identifier_node.append(etree.SubElement(identifier_node, "value", value=value_value))
    return identifier_node


def build_connection_type(system_value: str, code_value: str, display_value: str):
    connection_type = etree.Element("connectionType")
    connection_type.append(etree.SubElement(connection_type, "system", value=system_value))
    connection_type.append(etree.SubElement(connection_type, "code", value=code_value))
    connection_type.append(etree.SubElement(connection_type, "display", value=display_value))
    return connection_type


def build_managing_organization(system_value: str, value_value: str):
    managing_organization = etree.Element("managingOrganization")
    managing_organization.append(build_identifier_node(system_value, value_value))
    return managing_organization


def build_payload_type(system_value: str, code_value: str, display_value: str):
    payload_type = etree.Element("payloadType")
    coding = etree.Element("coding")
    coding.append(etree.SubElement(coding, "system", value=system_value))
    coding.append(etree.SubElement(coding, "code", value=code_value))
    coding.append(etree.SubElement(coding, "display", value=display_value))
    payload_type.append(coding)
    return payload_type


def array_to_string(combined_info: Dict, key: str):
    return str(combined_info.get(key)).strip("['']")
