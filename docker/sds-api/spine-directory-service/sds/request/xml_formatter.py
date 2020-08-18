from lxml import etree

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


def get_xml_format():
    root = build_root_element()
    root.append(etree.Element("id", value="f0f0e921-92ca-4a88-a550-2dbb36f703af"))
    root.append(build_extension_node())
    root.append(build_comment("NhsEndpointServiceId"))
    root.append(build_identifier_node(nhs_endpoint_serviceId_url, "urn:nhs:names:services:psis:REPC_IN150016UK05"))
    root.append(build_comment("NhsMhsFQDN"))
    root.append(build_identifier_node(nhs_mhs_fqdn_url, "192.168.128.11"))
    root.append(build_comment("NhsMhsEndPoint"))
    root.append(build_identifier_node(nhs_mhs_endpoint_url, "https://192.168.128.11/reliablemessaging/reliablerequest"))
    root.append(build_comment("NhsMhsPartyKey"))
    root.append(build_identifier_node(nhs_mhs_partykey_url, "R8008-0000806"))
    root.append(build_comment("NhsMhsCPAId"))
    root.append(build_identifier_node(nhs_mhs_cpaid_url, "S20001A000182"))
    root.append(build_comment("NhsSpineASID"))
    root.append(build_identifier_node(nhs_spine_asid_url, "227319907548"))
    root.append(etree.Element("status", value="active"))
    root.append(build_connection_type(connection_type_url, "hl7-fhir-msg", "HL7 FHIR Messaging"))
    root.append(build_managing_organization(managing_organization_url, "R8008"))
    root.append(build_payload_type(payload_type_url, "any", "Any"))

    root.append(etree.Element("address", value="https://192.168.128.11/"))

    tree = etree.tostring(root, pretty_print=False, xml_declaration=True, encoding="UTF-8")
    return tree


def build_root_element():
    attr_qname = etree.QName(schemaLocation_url, "schemaLocation")
    return etree.Element("Endpoint", {attr_qname: attr_qname_url}, nsmap={None: default_url, 'xsi': xsi_url})


def build_extension_node():
    extension_node = etree.Element('extension', url=extension_url)
    extension_node.append(build_string_extension("nhsMHSSyncReplyMode", "MSHSignalsOnly"))
    extension_node.append(build_string_extension("nhsMHSRetryInterval", "PT1M"))
    extension_node.append(build_integer_extension("nhsMHSRetries", "2"))
    extension_node.append(build_string_extension("nhsMHSPersistDuration", "PT5M"))
    extension_node.append(build_string_extension("nhsMHSDuplicateElimination", "always"))
    extension_node.append(build_string_extension("nhsMHSAckRequested", "always"))
    return extension_node


def build_string_extension(url: str, value: str):
    extension_sub = etree.Element("extension", url=url)
    extension_sub.append(etree.SubElement(extension_sub, "valueString", value=value))
    return extension_sub


def build_integer_extension(url: str, value: str):
    extension_sub = etree.Element("extension", url=url)
    extension_sub.append(etree.SubElement(extension_sub, "valueInteger", value=value))
    return extension_sub


def build_comment(comment: str):
    return etree.Comment(" " + comment + " ")


def build_identifier_node(system_value: str, value_value: str):
    identifier_node = etree.Element('identifier')
    identifier_node.append(etree.SubElement(identifier_node, "system", value=system_value))
    identifier_node.append(etree.SubElement(identifier_node, "value", value=value_value))
    return identifier_node


def build_connection_type(system_value: str, code_value: str, display_value: str):
    connection_type = etree.Element('connectionType')
    connection_type.append(etree.SubElement(connection_type, "system", value=system_value))
    connection_type.append(etree.SubElement(connection_type, "code", value=code_value))
    connection_type.append(etree.SubElement(connection_type, "display", value=display_value))
    return connection_type


def build_managing_organization(system_value: str, value_value: str):
    managing_organization = etree.Element('managingOrganization')
    managing_organization.append(build_identifier_node(system_value, value_value))
    return managing_organization


def build_payload_type(system_value: str, code_value: str, display_value: str):
    payload_type = etree.Element('payloadType')
    coding = etree.Element('coding')
    coding.append(etree.SubElement(coding, "system", value=system_value))
    coding.append(etree.SubElement(coding, "code", value=code_value))
    coding.append(etree.SubElement(coding, "display", value=display_value))
    payload_type.append(coding)
    return payload_type