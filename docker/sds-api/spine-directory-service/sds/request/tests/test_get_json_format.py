import json
from os import path
from unittest import TestCase

from request.fhir_json_mapper import build_endpoint_resource
from utilities import message_utilities

FILE_PATH = path.join(path.dirname(__file__), "examples/SDS-Endpoint-Example.json")
FIXED_UUID = "f0f0e921-92ca-4a88-a550-2dbb36f703af"
ORG_CODE = "R8008"
SERVICE_ID = "urn:nhs:names:services:psis:REPC_IN150016UK05"
LDAP_ATTRIBUTES = {
    "nhsMHSAckRequested": "always",
    "nhsMHSDuplicateElimination": "always",
    "nhsMHSEndPoint": [
        "https://192.168.128.11/reliablemessaging/reliablerequest",
        "https://192.168.128.50/reliablemessaging/something_else"
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


class TestGetJsonFormat(TestCase):

    def test_get_json_format(self):
        example = json.loads(open(FILE_PATH, "r").read())
        actual = build_endpoint_resource(LDAP_ATTRIBUTES, ORG_CODE, SERVICE_ID)
        actual = json.dumps(actual, indent=2)
        actual = json.loads(message_utilities.replace_uuid(actual, FIXED_UUID))

        self.assertEqual(example, actual)

    def test_get_json_format_with_empty_values_throws_no_exception(self):
        build_endpoint_resource(COMBINED_INFO_EMPTY, ORG_CODE, SERVICE_ID)
