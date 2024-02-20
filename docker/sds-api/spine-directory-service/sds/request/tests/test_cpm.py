import json
import os
import tornado.web

from unittest import TestCase
from request.cpm import transform_device_to_SDS, filter_cpm_devices_response
from lookup.sds_exception import SDSException

class TestCPM(TestCase):
    
    @staticmethod
    def _read_file(file):
        with open(file, 'r') as f:
            return json.load(f)
    
    def test_filter_results_unsuccessful_missing_required_device(self):
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("test_data", "cpm", "returned_devices.json"))
        incoming_json = self._read_file(dir_path)
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
                filter_cpm_devices_response(incoming_json, filt)
            self.assertEqual(str(context.exception), 'org_code and interaction_id must be provided')
    
    def test_filter_results_successful_required_device(self):
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("test_data", "cpm", "returned_devices.json"))
        incoming_json = self._read_file(dir_path)
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
        ]
        expected = [
            "filtered_device.json",
            "filtered_device.json",
            "filtered_device.json",
            "filtered_device.json",
            "filtered_device2.json",
            "filtered_device2.json",
            "filtered_device2.json",
            "filtered_device2.json"
        ]
        for index, filt in enumerate(filters):
            exp = self._read_file(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("test_data", "cpm", expected[index])))
            filtered_data = filter_cpm_devices_response(incoming_json, filt)
            assert len(filtered_data) == 1
            self.assertEqual(filtered_data, exp)
    
    def test_filter_results_no_results_required_device(self):
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("test_data", "cpm", "returned_devices.json"))
        incoming_json = self._read_file(dir_path)
        filters = [
            {
                "org_code": "5NR",
                "interaction_id": "urn:nhs:names:services:lrs:DOESNT_EXIST",
            },
            {
                "org_code": "FOO",
                "interaction_id": "urn:nhs:names:services:lrs:MCCI_IN010000UK13",
            },
            {
                "org_code": "5NR",
                "interaction_id": "urn:nhs:names:services:lrs:MCCI_IN010000UK13",
                "party_key": "5NR-801831",
                "manufacturing_organization": "BAR"
            },
            {
                "org_code": "5NR",
                "interaction_id": "urn:nhs:names:services:lrs:MCCI_IN010000UK13",
                "party_key": "FOO",
                "manufacturing_organization": "LSP02"
            },
            {
                "org_code": "5NR",
                "interaction_id": "urn:nhs:names:services:lrs:MCCI_IN010000UK13",
                "party_key": "FOO",
            },
            {
                "org_code": "5NR",
                "interaction_id": "urn:nhs:names:services:lrs:MCCI_IN010000UK13",
                "manufacturing_organization": "BAR"
            }
        ]
        expected = []
        for filt in filters:
            filtered_data = filter_cpm_devices_response(incoming_json, filt)
            assert len(filtered_data) == 0
            self.assertEqual(filtered_data, expected)
        
    
    def test_translated_device_data_device(self):
        expected = [
            {
                'nhsAsClient': ['5NR'],
                'nhsAsSvcIA': [
                    'urn:nhs:names:services:lrs:MCCI_IN010000UK13', 
                    'urn:nhs:names:services:lrs:QUPC_IN010000UK01', 
                    'urn:nhs:names:services:lrs:QUPC_IN010000UK15', 
                    'urn:nhs:names:services:lrs:QUPC_IN030000UK14', 
                    'urn:nhs:names:services:lrs:QUPC_IN040000UK14', 
                    'urn:nhs:names:services:lrs:QUQI_IN010000UK14', 
                    'urn:nhs:names:services:lrs:REPC_IN010000UK01', 
                    'urn:nhs:names:services:lrs:REPC_IN010000UK15', 
                    'urn:nhs:names:services:lrs:REPC_IN020000UK01', 
                    'urn:nhs:names:services:lrs:REPC_IN020000UK13', 
                    'urn:nhs:names:services:lrs:REPC_IN030000UK01', 
                    'urn:nhs:names:services:lrs:REPC_IN040000UK01', 
                    'urn:nhs:names:services:lrs:REPC_IN040000UK15', 
                    'urn:nhs:names:services:lrs:REPC_IN050000UK01', 
                    'urn:nhs:names:services:lrs:REPC_IN050000UK13', 
                    'urn:nhs:names:services:lrs:REPC_IN060000UK01', 
                    'urn:nhs:names:services:lrs:REPC_IN070000UK01', 
                    'urn:nhs:names:services:lrs:REPC_IN080000UK01', 
                    'urn:nhs:names:services:lrs:REPC_IN110000UK01', 
                    'urn:nhs:names:services:lrsquery:MCCI_IN010000UK13', 
                    'urn:nhs:names:services:lrsquery:QUPC_IN030000UK14', 
                    'urn:nhs:names:services:lrsquery:QUPC_IN040000UK14', 
                    'urn:nhs:names:services:lrsquery:QUQI_IN010000UK14', 
                    'urn:oasis:names:tc:ebxml-msg:service:Acknowledgment', 
                    'urn:oasis:names:tc:ebxml-msg:service:MessageError'
                ], 
                'nhsMhsManufacturerOrg': 'LSP02', 
                'nhsMhsPartyKey': '5NR-801831', 
                'nhsIdCode': '5NR', 
                'uniqueIdentifier': '010057927542'
            }
        ]
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("test_data", "cpm", "filtered_device.json"))
        incoming_json = self._read_file(dir_path)
        translated_data = transform_device_to_SDS(incoming_json)
        self.assertEqual(translated_data, expected)
    
    def test_translated_device_data_multiple_devices(self):
        expected = [
            {
                'nhsAsClient': ['5NR'],
                'nhsAsSvcIA': [
                    'urn:nhs:names:services:lrs:MCCI_IN010000UK13', 
                    'urn:nhs:names:services:lrs:QUPC_IN010000UK01', 
                    'urn:nhs:names:services:lrs:QUPC_IN010000UK15', 
                    'urn:nhs:names:services:lrs:QUPC_IN030000UK14', 
                    'urn:nhs:names:services:lrs:QUPC_IN040000UK14', 
                    'urn:nhs:names:services:lrs:QUQI_IN010000UK14', 
                    'urn:nhs:names:services:lrs:REPC_IN010000UK01', 
                    'urn:nhs:names:services:lrs:REPC_IN010000UK15', 
                    'urn:nhs:names:services:lrs:REPC_IN020000UK01', 
                    'urn:nhs:names:services:lrs:REPC_IN020000UK13', 
                    'urn:nhs:names:services:lrs:REPC_IN030000UK01', 
                    'urn:nhs:names:services:lrs:REPC_IN040000UK01', 
                    'urn:nhs:names:services:lrs:REPC_IN040000UK15', 
                    'urn:nhs:names:services:lrs:REPC_IN050000UK01', 
                    'urn:nhs:names:services:lrs:REPC_IN050000UK13', 
                    'urn:nhs:names:services:lrs:REPC_IN060000UK01', 
                    'urn:nhs:names:services:lrs:REPC_IN070000UK01', 
                    'urn:nhs:names:services:lrs:REPC_IN080000UK01', 
                    'urn:nhs:names:services:lrs:REPC_IN110000UK01', 
                    'urn:nhs:names:services:lrsquery:MCCI_IN010000UK13', 
                    'urn:nhs:names:services:lrsquery:QUPC_IN030000UK14', 
                    'urn:nhs:names:services:lrsquery:QUPC_IN040000UK14', 
                    'urn:nhs:names:services:lrsquery:QUQI_IN010000UK14', 
                    'urn:oasis:names:tc:ebxml-msg:service:Acknowledgment', 
                    'urn:oasis:names:tc:ebxml-msg:service:MessageError'
                ], 
                'nhsMhsManufacturerOrg': 'LSP02', 
                'nhsMhsPartyKey': '5NR-801831', 
                'nhsIdCode': '5NR', 
                'uniqueIdentifier': '010057927542'
            },
            {
                'nhsAsClient': ['5NR'],
                'nhsAsSvcIA': [
                    'urn:nhs:names:services:pds:MCCI_IN010000UK13',
                    'urn:nhs:names:services:pds:PRPA_IN150000UK30',
                    'urn:nhs:names:services:pds:PRPA_IN060000UK30',
                    'urn:nhs:names:services:pds:PRPA_IN040000UK30',
                    'urn:nhs:names:services:pds:PRPA_IN160000UK30',
                    'urn:nhs:names:services:pds:PRPA_IN000206UK01',
                    'urn:nhs:names:services:pds:PRPA_IN000207UK05',
                    'urn:nhs:names:services:pds:PRPA_IN000205UK05',
                    'urn:nhs:names:services:pds:PRPA_IN000208UK03',
                    'urn:nhs:names:services:pdsquery:QUPA_IN050000UK32',
                    'urn:nhs:names:services:pdsquery:QUPA_IN010000UK32',
                    'urn:nhs:names:services:lrsquery:QUPC_IN040000UK14',
                    'urn:nhs:names:services:pdsquery:MCCI_IN010000UK13',
                    'urn:nhs:names:services:pdsquery:QUPA_IN030000UK32',
                    'urn:nhs:names:services:pdsquery:QUPA_IN020000UK31',
                    'urn:nhs:names:services:pdsquery:QUPA_IN040000UK32',
                    'urn:oasis:names:tc:ebxml-msg:service:Acknowledgment',
                    'urn:oasis:names:tc:ebxml-msg:service:MessageError',
                    'urn:nhs:names:services:ebs:PRSC_IN040000UK08',
                    'urn:nhs:names:services:ebs:PRSC_IN060000UK06',
                    'urn:nhs:names:services:ebs:PRSC_IN140000UK06',
                    'urn:nhs:names:services:ebs:PRSC_IN150000UK06',
                    'urn:nhs:names:services:ebs:PRSC_IN070000UK08',
                    'urn:nhs:names:services:ebs:PRSC_IN080000UK07',
                    'urn:nhs:names:services:ebs:PRSC_IN050000UK06',
                ], 
                'nhsMhsManufacturerOrg': 'LSP02', 
                'nhsMhsPartyKey': '5NR-801831', 
                'nhsIdCode': '5NR', 
                'uniqueIdentifier': '798706756516'
            }
        ]
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("test_data", "cpm", "filtered_devices.json"))
        incoming_json = self._read_file(dir_path)
        translated_data = transform_device_to_SDS(incoming_json)
        assert len(translated_data) == 2
        self.assertEqual(translated_data, expected)
