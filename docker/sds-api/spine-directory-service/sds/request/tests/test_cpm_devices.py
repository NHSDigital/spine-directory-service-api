import json
import os
import requests
import tornado.web
import unittest

from unittest import TestCase
from unittest.mock import patch
from jsonschema import validate
from request.cpm import DeviceCpm, process_cpm_device_request, CpmClient, get_device_from_cpm, DeviceCpmClient
from request.tests.test_data.cpm.schema import device_schema_json
from lookup.sds_exception import SDSException

RETURNED_DEVICES_JSON = "returned_devices_single.json"
RETURNED_DEVICES_MULTIPLE_JSON = "returned_devices_multiple.json"

EXPECTED_LDAP_1 = {
    'nhsAsClient': ['5NR'],
    'nhsAsSvcIA': [
    'urn:oasis:names:tc:ebxml-msg:service:Acknowledgment',
    'urn:oasis:names:tc:ebxml-msg:service:MessageError',
    'urn:nhs:names:services:lrs:REPC_IN020000UK01',
    'urn:nhs:names:services:lrs:REPC_IN050000UK01',
    'urn:nhs:names:services:lrs:REPC_IN040000UK01',
    'urn:nhs:names:services:lrs:REPC_IN030000UK01',
    'urn:nhs:names:services:lrs:QUPC_IN010000UK01',
    'urn:nhs:names:services:lrs:REPC_IN050000UK13',
    'urn:nhs:names:services:lrs:REPC_IN060000UK01',
    'urn:nhs:names:services:lrs:REPC_IN080000UK01',
    'urn:nhs:names:services:lrs:QUQI_IN010000UK14',
    'urn:nhs:names:services:lrs:QUPC_IN030000UK14',
    'urn:nhs:names:services:lrs:QUPC_IN010000UK15',
    'urn:nhs:names:services:lrs:QUPC_IN040000UK14',
    'urn:nhs:names:services:lrs:REPC_IN070000UK01',
    'urn:nhs:names:services:lrs:REPC_IN010000UK01',
    'urn:nhs:names:services:lrs:REPC_IN110000UK01',
    'urn:nhs:names:services:lrs:REPC_IN020000UK13',
    'urn:nhs:names:services:lrs:REPC_IN010000UK15',
    'urn:nhs:names:services:lrs:MCCI_IN010000UK13',
    'urn:nhs:names:services:lrs:REPC_IN040000UK15',
    'urn:nhs:names:services:lrsquery:QUPC_IN040000UK14',
    'urn:nhs:names:services:lrsquery:QUPC_IN030000UK14',
    'urn:nhs:names:services:lrsquery:QUQI_IN010000UK14',
    'urn:nhs:names:services:lrsquery:MCCI_IN010000UK13'
    ],
    'nhsMhsManufacturerOrg': 'LSP02',
    'nhsMhsPartyKey': '5NR-801831',
    'nhsIdCode': '5NR',
    'uniqueIdentifier': ['010057927542']
}

EXPECTED_LDAP_2 = {
    'nhsAsClient': ['RTX'],
    'nhsAsSvcIA': [
    'urn:oasis:names:tc:ebxml-msg:service:Acknowledgment',
    'urn:oasis:names:tc:ebxml-msg:service:MessageError',
    'urn:nhs:names:services:ebs:PRSC_IN040000UK08',
    'urn:nhs:names:services:ebs:PRSC_IN060000UK06',
    'urn:nhs:names:services:ebs:PRSC_IN140000UK06',
    'urn:nhs:names:services:ebs:PRSC_IN150000UK06',
    'urn:nhs:names:services:ebs:PRSC_IN070000UK08',
    'urn:nhs:names:services:ebs:PRSC_IN080000UK07',
    'urn:nhs:names:services:ebs:PRSC_IN050000UK06',
    'urn:nhs:names:services:ebs:PRSC_IN090000UK09',
    'urn:nhs:names:services:ebs:PRSC_IN130000UK07',
    'urn:nhs:names:services:ebs:PRSC_IN110000UK08',
    'urn:nhs:names:services:ebs:PRSC_IN100000UK06',
    'urn:nhs:names:services:ebs:MCCI_IN010000UK13',
    'urn:nhs:names:services:pds:MCCI_IN010000UK13',
    'urn:nhs:names:services:pds:PRPA_IN150000UK30',
    'urn:nhs:names:services:pds:PRPA_IN060000UK30',
    'urn:nhs:names:services:pds:PRPA_IN040000UK30',
    'urn:nhs:names:services:pds:PRPA_IN160000UK30',
    'urn:nhs:names:services:pdsquery:QUPA_IN060000UK30',
    'urn:nhs:names:services:pdsquery:QUPA_IN050000UK32',
    'urn:nhs:names:services:pdsquery:QUPA_IN010000UK32',
    'urn:nhs:names:services:pdsquery:QUPA_IN070000UK30',
    'urn:nhs:names:services:pdsquery:QUQI_IN010000UK14',
    'urn:nhs:names:services:pdsquery:QUPA_IN030000UK32',
    'urn:nhs:names:services:pdsquery:QUPA_IN020000UK31',
    'urn:nhs:names:services:pdsquery:QUPA_IN040000UK32',
    'urn:nhs:names:services:pdsquery:MCCI_IN010000UK13',
    'urn:nhs:names:services:psisquery:QUPC_IN160101UK05',
    'urn:nhs:names:services:psisquery:QUPC_IN160109UK05',
    'urn:nhs:names:services:psisquery:QUPC_IN160102UK05',
    'urn:nhs:names:services:psisquery:QUPC_IN160104UK05',
    'urn:nhs:names:services:psisquery:QUPC_IN160108UK05',
    'urn:nhs:names:services:psisquery:QUPC_IN160110UK05',
    'urn:nhs:names:services:psisquery:MCCI_IN010000UK13',
    'urn:nhs:names:services:psisquery:QUQI_IN010000UK14',
    'urn:nhs:names:services:psisquery:QUPC_IN160107UK05',
    'urn:nhs:names:services:psisquery:QUPC_IN160103UK05',
    'urn:nhs:names:services:lrs:REPC_IN040000UK15',
    'urn:nhs:names:services:lrs:REPC_IN050000UK13',
    'urn:nhs:names:services:lrs:MCCI_IN010000UK13',
    'urn:nhs:names:services:lrs:QUQI_IN010000UK14',
    'urn:nhs:names:services:lrs:REPC_IN010000UK15',
    'urn:nhs:names:services:lrs:REPC_IN020000UK13',
    'urn:nhs:names:services:lrsquery:QUPC_IN010000UK32',
    'urn:nhs:names:services:lrsquery:QUQI_IN010000UK14',
    'urn:nhs:names:services:lrsquery:QUPC_IN020000UK17',
    'urn:nhs:names:services:lrsquery:QUPC_IN250000UK02',
    'urn:nhs:names:services:lrsquery:QUPC_IN060000UK32',
    'urn:nhs:names:services:lrsquery:QUPC_IN070000UK32',
    'urn:nhs:names:services:lrsquery:MCCI_IN010000UK13',
    'urn:nhs:names:services:lrsquery:QUPC_IN090000UK03',
    'urn:nhs:names:services:lrsquery:QUPC_IN030000UK14',
    'urn:nhs:names:services:sds:REPC_IN130005UK01',
    'urn:nhs:names:services:sds:REPC_IN130003UK01',
    'urn:nhs:names:services:sds:REPC_IN130004UK01',
    'urn:nhs:names:services:sds:REPC_IN130002UK01',
    'urn:nhs:names:services:sds:MCCI_IN010000UK13',
    'urn:nhs:names:services:sdsquery:QUPC_IN041234UK01',
    'urn:nhs:names:services:sdsquery:REPC_IN130007UK01',
    'urn:nhs:names:services:sdsquery:MCCI_IN010000UK13',
    'urn:nhs:names:services:sdsquery:QUPC_IN010102UK01',
    'urn:nhs:names:services:sdsquery:QUPC_IN010103UK01',
    'urn:nhs:names:services:sdsquery:QUQI_IN010000UK14',
    'urn:nhs:names:services:sdsquery:AccreditedSystemSearchRequest_1_0',
    'urn:nhs:names:services:sdsquery:AccreditedSystemSearchResponse_1_0'
    ],
    'nhsMhsManufacturerOrg': 'LSP02',
    'nhsMhsPartyKey': 'RTX-806845',
    'nhsIdCode': 'RTX',
    'uniqueIdentifier': ['798706756516']
}

class TestCPMDevice(TestCase):

    @staticmethod
    def _read_file(file):
        with open(file, 'r') as f:
            return json.load(f)

    @patch.dict(os.environ, {"USE_CPM": "1"})
    def test_filter_results_unsuccessful_missing_required_device(self):
        filters = [
            {
                "org_code": "",
                "interaction_id": "urn:nhs:names:services:lrs:MCCI_IN010000UK13",
            },
            {
                "org_code": "5NR",
                "interaction_id": "",
            },
            {
                "org_code": "",
                "interaction_id": "",
            },
            {
                "org_code": "",
                "interaction_id": "",
                "party_key": "5NR-801831"
            },
            {
                "org_code": "",
                "interaction_id": "",
                "manufacturing_organization": "LSP02"
            },
            {
                "interaction_id": "urn:nhs:names:services:lrs:MCCI_IN010000UK13",
            },
            {
                "org_code": "5NR",
            },
            {
            },
            {
                "party_key": "5NR-801831"
            },
            {
                "manufacturing_organization": "LSP02"
            },
        ]
        for filt in filters:
            with self.assertRaises(SDSException) as context:
                DeviceCpmClient(client_id="1234", apigee_url="https://foo.bar", query_params=filt)
            self.assertEqual(str(context.exception), 'org_code and interaction_id must be provided')

    @patch.dict(os.environ, {"USE_CPM": "1"})
    def test_filter_results_not_allowed(self):
        filters = [
            {
                "foo": "bar",
                "interaction_id": "urn:nhs:names:services:lrs:MCCI_IN010000UK13",
            },
            {
                "org_code": "5NR",
                "interaction_id": "urn:nhs:names:services:lrs:MCCI_IN010000UK13",
                "foo": "bar",
            },
            {
                "org_code": "5NR",
                "interaction_id": "urn:nhs:names:services:lrs:MCCI_IN010000UK13",
                "manufacturing_organization": "LSP02",
                "foo": "bar",
            },
            {
                "org_code": "5NR",
                "interaction_id": "urn:nhs:names:services:lrs:MCCI_IN010000UK13",
                "party_key": "5NR-801831",
                "foo": "bar",
            },
            {
                "org_code": "5NR",
                "interaction_id": "urn:nhs:names:services:lrs:MCCI_IN010000UK13",
                "party_key": "5NR-801831",
                "manufacturing_organization": "LSP02",
                "foo": "bar",
            },
            {
                "org_code": "RTX",
                "interaction_id": "urn:nhs:names:services:pds:PRPA_IN160000UK30",
                "foo": "bar",
            },
            {
                "org_code": "RTX",
                "interaction_id": "urn:nhs:names:services:pds:PRPA_IN160000UK30",
                "manufacturing_organization": "LSP02",
                "foo": "bar",
            },
            {
                "org_code": "RTX",
                "interaction_id": "urn:nhs:names:services:pds:PRPA_IN160000UK30",
                "party_key": "RTX-806845",
                "foo": "bar",
            },
            {
                "org_code": "RTX",
                "interaction_id": "urn:nhs:names:services:pds:PRPA_IN160000UK30",
                "party_key": "RTX-806845",
                "manufacturing_organization": "LSP02",
                "foo": "bar",
            },
        ]
        for filt in filters:
            with self.assertRaises(SDSException) as context:
                DeviceCpmClient(client_id="1234", apigee_url="https://foo.bar", query_params=filt)
            self.assertEqual(str(context.exception), "foo not allowed in filters")

    @patch.dict(os.environ, {"USE_CPM": "1"})
    def test_translated_device_data_device(self):
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("test_data", "cpm", RETURNED_DEVICES_JSON))
        incoming_json = self._read_file(dir_path)
        expected = [EXPECTED_LDAP_1]
        devices = DeviceCpm(incoming_json)
        translated_data = devices.transform_to_ldap()
        self.assertEqual(translated_data, expected)

    @patch.dict(os.environ, {"USE_CPM": "1"})
    def test_translated_device_data_multiple_devices(self):
        expected = [
            EXPECTED_LDAP_1,
            EXPECTED_LDAP_2
        ]
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("test_data", "cpm", RETURNED_DEVICES_MULTIPLE_JSON))
        incoming_json = self._read_file(dir_path)
        devices = DeviceCpm(incoming_json)
        translated_data = devices.transform_to_ldap()
        assert len(translated_data) == 2
        self.assertEqual(translated_data, expected)

    @patch.dict(os.environ, {"USE_CPM": "1"})
    def test_device_process_success(self):
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("test_data", "cpm", RETURNED_DEVICES_JSON))
        incoming_json = self._read_file(dir_path)
        expected = [EXPECTED_LDAP_1]
        result = process_cpm_device_request(incoming_json)
        self.assertEqual(result, expected)

    @patch.dict(os.environ, {"USE_CPM": "1"})
    def test_allowed_query_params(self):
        filters = [
            {
                "org_code": "5NR",
                "interaction_id": "urn:nhs:names:services:lrs:MCCI_IN010000UK13",
            },
            {
                "org_code": "5NR",
                "interaction_id": "urn:nhs:names:services:lrs:MCCI_IN010000UK13",
                "manufacturing_organization": "LSP02"
            },
            {
                "org_code": "5NR",
                "interaction_id": "urn:nhs:names:services:lrs:MCCI_IN010000UK13",
                "party_key": "5NR-801831"
            },
            {
                "org_code": "5NR",
                "interaction_id": "urn:nhs:names:services:lrs:MCCI_IN010000UK13",
                "party_key": "5NR-801831",
                "manufacturing_organization": "LSP02"
            },
            {
                "org_code": "RTX",
                "interaction_id": "urn:nhs:names:services:pds:PRPA_IN160000UK30",
            },
            {
                "org_code": "RTX",
                "interaction_id": "urn:nhs:names:services:pds:PRPA_IN160000UK30",
                "manufacturing_organization": "LSP02"
            },
            {
                "org_code": "RTX",
                "interaction_id": "urn:nhs:names:services:pds:PRPA_IN160000UK30",
                "party_key": "RTX-806845"
            },
            {
                "org_code": "RTX",
                "interaction_id": "urn:nhs:names:services:pds:PRPA_IN160000UK30",
                "party_key": "RTX-806845",
                "manufacturing_organization": "LSP02"
            },
            {
                "org_code": " RTX",
                "interaction_id": " urn:nhs:names:services:pds:PRPA_IN160000UK30",
                "party_key": " RTX-806845",
                "manufacturing_organization": " LSP02"
            },
            {
                "org_code": "RTX ",
                "interaction_id": "urn:nhs:names:services:pds:PRPA_IN160000UK30 ",
                "party_key": "RTX-806845 ",
                "manufacturing_organization": "LSP02 "
            }
        ]
        for query in filters:
            cpm_client = DeviceCpmClient(client_id="1234", apigee_url="https://foo.bar", query_params=query)
            assert "org_code" not in cpm_client._params
            assert "interaction_id" not in cpm_client._params
            assert "nhs_id_code" in cpm_client._params
            assert "nhs_as_svc_ia" in cpm_client._params
            assert cpm_client._params["nhs_id_code"] == query["org_code"].strip()
            assert cpm_client._params["nhs_as_svc_ia"] == query["interaction_id"].strip()
            if "party_key" in query:
                assert "party_key" not in cpm_client._params
                assert "nhs_mhs_party_key" in cpm_client._params
                assert cpm_client._params["nhs_mhs_party_key"] == query["party_key"].strip()
            if "manufacturing_organization" in query:
                assert "manufacturing_organization" not in cpm_client._params
                assert "nhs_mhs_manufacturer_org" in cpm_client._params
                assert cpm_client._params["nhs_mhs_manufacturer_org"] == query["manufacturing_organization"].strip()
            assert isinstance(cpm_client, DeviceCpmClient)
