from lxml import etree

schemaLocation_url = "http://www.w3.org/2001/XMLSchema-instance"
attr_qname_url = "http://hl7.org/fhir file:///C:/Validation-Assets-R4/Schemas/fhir-all-xsd/fhir-all.xsd"
default_url = "http://hl7.org/fhir"
xsi_url = "http://www.w3.org/2001/XMLSchema-instance"
extension_url = "https://fhir.nhs.uk/R4/StructureDefinition/Extension-SDS-ReliabilityConfiguration"


def get_xml_format():
    root = build_root_element()
    root.append(etree.Element("id", value="to-be-defined"))
    root.append(build_extension_node())

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
