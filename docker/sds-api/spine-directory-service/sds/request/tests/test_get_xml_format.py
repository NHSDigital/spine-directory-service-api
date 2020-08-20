from unittest import TestCase

from request.xml_formatter import get_xml_format

ORG_CODE = "R8008"
SERVICE_ID = "urn:nhs:names:services:psis:REPC_IN150016UK05"
COMBINED_INFO = {
    "nhsMHSAckRequested": "always",
    "nhsMHSDuplicateElimination": "always",
    "nhsMHSEndPoint": [
        "https://192.168.128.11/reliablemessaging/reliablerequest"
    ],
    "nhsMHSPartyKey": "R8008-0000806",
    "nhsMHSPersistDuration": ["PT5M"],
    "nhsMHSRetries": [2],
    "nhsMHSRetryInterval": ["PT1M"],
    "nhsMHSSyncReplyMode": "MSHSignalsOnly",
    "nhsMhsCPAId": "S20001A000182",
    "nhsMhsFQDN": "192.168.128.11",
    "uniqueIdentifier": [
        "227319907548"
    ]
}

COMBINED_INFO_EMPTY = {
    "nhsMHSAckRequested": "",
    "nhsMHSDuplicateElimination": "",
    "nhsMHSEndPoint": [],
    "nhsMHSPartyKey": "",
    "nhsMHSPersistDuration": [],
    "nhsMHSRetries": [],
    "nhsMHSRetryInterval": [],
    "nhsMHSSyncReplyMode": "",
    "nhsMhsCPAId": "",
    "nhsMhsFQDN": "",
    "uniqueIdentifier": []
}


class TestGetXmlFormat(TestCase):

    def test_get_xml_format(self):
        example = open("examples/SDS-Endpoint-Example.xml", "r").read()
        self.assertEqual(example, get_xml_format(COMBINED_INFO, ORG_CODE, SERVICE_ID))

    def test_get_xml_format_with_empty_values_throws_no_exception(self):
        get_xml_format(COMBINED_INFO_EMPTY, ORG_CODE, SERVICE_ID)
