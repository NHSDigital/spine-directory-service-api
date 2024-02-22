import json
import os
import tornado.web

from unittest import TestCase
from request.cpm import EndpointCpm, process_cpm_endpoint_request

class TestCPMEndpoints(TestCase):
    RETURNED_ENDPOINTS_JSON = "returned_endpoints.json"
    FILTERED_ENDPOINT_1 = "filtered_endpoint.json"
    FILTERED_ENDPOINT_2 = "filtered_endpoint2.json"
    FILTERED_ENDPOINTS = "filtered_endpoints.json"
    
    @staticmethod
    def _read_file(file):
        with open(file, 'r') as f:
            return json.load(f)
    
    def test_filter_results_unsuccessful_missing_required_endpoint(self):
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("test_data", "cpm", RETURNED_ENDPOINTS_JSON))
        incoming_json = self._read_file(dir_path)
        filters = [
            
            {
                "org_code": "",
                "service_id": "urn:nhs:names:services:ebs:PRSC_IN070000UK08",
            },
            {
                "org_code": "RTX",
                "service_id": "",
            },
            {
                "org_code": "",
                "party_key": "RTX-821088"
            },
            {
                "service_id": "",
                "party_key": "RTX-821088"
            },
            {
                "service_id": "urn:nhs:names:services:ebs:PRSC_IN070000UK08",
                "party_key": ""
            },
            {
                "org_code": "",
                "service_id": "",
            },
            {
                "org_code": "",
                "party_key": "",
            },
            {
                "service_id": "",
                "party_key": ""
            },
            {
            },
            {
                "service_id": "urn:nhs:names:services:ebs:PRSC_IN070000UK08",
            },
            {
                "org_code": "RTX",
            },
            {
                "party_key": "RTX-821088"
            },
            {
                "org_code": "",
                "service_id": "urn:nhs:names:services:ebs:PRSC_IN070000UK08",
                "party_key": ""
            },
            {
                "org_code": "RTX",
                "service_id": "",
                "party_key": ""
            },
            {
                "org_code": "",
                "service_id": "",
                "party_key": "RTX-821088"
            },
            {
                "org_code": "",
                "service_id": "",
                "party_key": ""
            }
        ]
        for filt in filters:
            with self.assertRaises(tornado.web.HTTPError) as context:
                EndpointCpm(incoming_json, filt)
            raised_exception = context.exception
            self.assertEqual(raised_exception.status_code, 400)
            self.assertEqual(raised_exception.log_message, 'Missing or invalid query parameters. Should one of following combinations: [\'organization=https://fhir.nhs.uk/Id/ods-organization-code|value&identifier=https://fhir.nhs.uk/Id/nhsServiceInteractionId|value&identifier=https://fhir.nhs.uk/Id/nhsMhsPartyKey|value\'\'organization=https://fhir.nhs.uk/Id/ods-organization-code|value&identifier=https://fhir.nhs.uk/Id/nhsServiceInteractionId|value\'\'organization=https://fhir.nhs.uk/Id/ods-organization-code|value&identifier=https://fhir.nhs.uk/Id/nhsMhsPartyKey|value\'\'identifier=https://fhir.nhs.uk/Id/nhsServiceInteractionId|value&identifier=https://fhir.nhs.uk/Id/nhsMhsPartyKey|value\']')
    
    def test_filter_results_successful_required_endpoints(self):
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("test_data", "cpm", RETURNED_ENDPOINTS_JSON))
        incoming_json = self._read_file(dir_path)
        filters = [
            {
                "org_code": "RTX",
                "service_id": "urn:nhs:names:services:ebs:PRSC_IN070000UK08",
            },
            {
                "org_code": "RTX",
                "service_id": "urn:nhs:names:services:ebs:PRSC_IN070000UK08",
                "party_key": "RTX-821088"
            },
            {
                "service_id": "urn:nhs:names:services:ebs:PRSC_IN070000UK08",
                "party_key": "RTX-821088"
            },
            {
                "org_code": "RTX",
                "service_id": "urn:nhs:names:services:cpisquery:REPC_IN000007GB01",
            },
            {
                "org_code": "RTX",
                "service_id": "urn:nhs:names:services:cpisquery:REPC_IN000007GB01",
                "party_key": "RTX-821088"
            },
            {
                "service_id": "urn:nhs:names:services:cpisquery:REPC_IN000007GB01",
                "party_key": "RTX-821088"
            }
        ]
        expected = [
            FILTERED_ENDPOINT_1,
            FILTERED_ENDPOINT_1,
            FILTERED_ENDPOINT_1,
            FILTERED_ENDPOINT_2,
            FILTERED_ENDPOINT_2,
            FILTERED_ENDPOINT_2
        ]
        for index, filt in enumerate(filters):
            exp = self._read_file(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("test_data", "cpm", expected[index])))
            endpoints = EndpointCpm(incoming_json, filt)
            filtered_data = endpoints.filter_cpm_response()
            assert len(filtered_data) == 1
            self.assertEqual(filtered_data, exp)
    
    def test_filter_results_no_results_required_endpoint(self):
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("test_data", "cpm", RETURNED_ENDPOINTS_JSON))
        incoming_json = self._read_file(dir_path)
        filters = [
            {
                "org_code": "RTX",
                "service_id": "urn:nhs:names:services:lrs:DOESNT_EXIST",
            },
            {
                "org_code": "FOO",
                "service_id": "urn:nhs:names:services:cpisquery:REPC_IN000007GB01",
            },
            {
                "org_code": "RTX",
                "service_id": "urn:nhs:names:services:cpisquery:REPC_IN000007GB01",
                "party_key": "BAR"
            },
            {
                "org_code": "RTX",
                "party_key": "BAR"
            },
            {
                "org_code": "FOO",
                "service_id": "urn:nhs:names:services:lrs:DOESNT_EXIST",
                "party_key": "BAR"
            },
            {
                "org_code": "RTX",
                "service_id": "urn:nhs:names:services:lrs:DOESNT_EXIST",
                "party_key": "RTX-821088"
            },
            {
                "org_code": "FOO",
                "service_id": "urn:nhs:names:services:cpisquery:REPC_IN000007GB01",
                "party_key": "RTX-821088"
            },
            {
                "org_code": "RTX",
                "service_id": "urn:nhs:names:services:cpisquery:REPC_IN000007GB01",
                "party_key": "BAR"
            },
        ]
        expected = []
        for filt in filters:
            endpoints = EndpointCpm(incoming_json, filt)
            filtered_data = endpoints.filter_cpm_response()
            assert len(filtered_data) == 0
            self.assertEqual(filtered_data, expected)

    def test_translated_endpoint_data_endpoint(self):
        filt = {
            "org_code": "RTX",
            "interaction_id": "urn:nhs:names:services:lrs:MCCI_IN010000UK13"
        }
        expected = [
            {
                'nhsIDCode': 'RTX',
                'nhsMHSAckRequested': 'always',
                'nhsMhsActor': ['urn:oasis:names:tc:ebxml-msg:actor:nextMSH'],
                'nhsMhsCPAId': '69720694737ed98c0242',
                'nhsMHSDuplicateElimination': 'always',
                'nhsMHSEndPoint': ['https://msg65-spine.msg.mpe.ncrs.nhs.uk/MHS/RTX/EBS3-5/messagehandler'],
                'nhsMhsFQDN': 'msg65-spine.msg.mpe.ncrs.nhs.uk',
                'nhsMHsIN': 'PRSC_IN070000UK08',
                'nhsMHSPartyKey': 'RTX-821088',
                'nhsMHSPersistDuration': 'PT4M',
                'nhsMHSRetries': 2,
                'nhsMHSRetryInterval': 'PT2S',
                'nhsMHsSN': 'urn:nhs:names:services:ebs',
                'nhsMhsSvcIA': 'urn:nhs:names:services:ebs:PRSC_IN070000UK08',
                'nhsMHSSyncReplyMode': 'None',
                'uniqueIdentifier': ['69720694737ed98c0242']
            }
        ]
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("test_data", "cpm", FILTERED_ENDPOINT_1))
        incoming_json = self._read_file(dir_path)
        endpoints = EndpointCpm(incoming_json, filt)
        translated_data = endpoints.transform_to_ldap(incoming_json)
        self.assertEqual(translated_data, expected)

    def test_translated_device_data_multiple_devices(self):
        filt = {
            "org_code": "5NR",
            "party_key": "RTX-821088"
        }
        expected = [
            {
                'nhsIDCode': 'RTX',
                'nhsMHSAckRequested': 'always',
                'nhsMhsActor': ['urn:oasis:names:tc:ebxml-msg:actor:nextMSH'],
                'nhsMhsCPAId': '69720694737ed98c0242',
                'nhsMHSDuplicateElimination': 'always',
                'nhsMHSEndPoint': ['https://msg65-spine.msg.mpe.ncrs.nhs.uk/MHS/RTX/EBS3-5/messagehandler'],
                'nhsMhsFQDN': 'msg65-spine.msg.mpe.ncrs.nhs.uk',
                'nhsMHsIN': 'PRSC_IN070000UK08',
                'nhsMHSPartyKey': 'RTX-821088',
                'nhsMHSPersistDuration': 'PT4M',
                'nhsMHSRetries': 2,
                'nhsMHSRetryInterval': 'PT2S',
                'nhsMHsSN': 'urn:nhs:names:services:ebs',
                'nhsMhsSvcIA': 'urn:nhs:names:services:ebs:PRSC_IN070000UK08',
                'nhsMHSSyncReplyMode': 'None',
                'uniqueIdentifier': ['69720694737ed98c0242']
            },
            {
                'nhsIDCode': 'RTX',
                'nhsMHSAckRequested': 'never',
                'nhsMhsActor': [],
                'nhsMhsCPAId': '798bc45334bbb95b51de',
                'nhsMHSDuplicateElimination': 'never',
                'nhsMHSEndPoint': ['https://msg65-spine.msg.mpe.ncrs.nhs.uk/Tower6-2/RTX/CPIS-0/responsehandler'],
                'nhsMhsFQDN': 'msg65-spine.msg.mpe.ncrs.nhs.uk',
                'nhsMHsIN': 'REPC_IN000007GB01',
                'nhsMHSPartyKey': 'RTX-821088',
                'nhsMHSPersistDuration': '',
                'nhsMHSRetries': 0,
                'nhsMHSRetryInterval': '',
                'nhsMHsSN': 'urn:nhs:names:services:cpisquery',
                'nhsMhsSvcIA': 'urn:nhs:names:services:cpisquery:REPC_IN000007GB01',
                'nhsMHSSyncReplyMode': 'MSHSignalsOnly',
                'uniqueIdentifier': ['798bc45334bbb95b51de']
            }
        ]
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("test_data", "cpm", FILTERED_ENDPOINTS))
        incoming_json = self._read_file(dir_path)
        endpoints = EndpointCpm(incoming_json, filt)
        translated_data = endpoints.transform_to_ldap(incoming_json)
        assert len(translated_data) == 2
        self.assertEqual(translated_data, expected)

    def test_translated_endpoint_full_process(self):
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("test_data", "cpm", RETURNED_ENDPOINTS_JSON))
        incoming_json = self._read_file(dir_path)
        filt = {
            "org_code": "RTX",
            "service_id": "urn:nhs:names:services:ebs:PRSC_IN070000UK08",
        }
        expected = [
            {
                'nhsIDCode': 'RTX',
                'nhsMHSAckRequested': 'always',
                'nhsMhsActor': ['urn:oasis:names:tc:ebxml-msg:actor:nextMSH'],
                'nhsMhsCPAId': '69720694737ed98c0242',
                'nhsMHSDuplicateElimination': 'always',
                'nhsMHSEndPoint': ['https://msg65-spine.msg.mpe.ncrs.nhs.uk/MHS/RTX/EBS3-5/messagehandler'],
                'nhsMhsFQDN': 'msg65-spine.msg.mpe.ncrs.nhs.uk',
                'nhsMHsIN': 'PRSC_IN070000UK08',
                'nhsMHSPartyKey': 'RTX-821088',
                'nhsMHSPersistDuration': 'PT4M',
                'nhsMHSRetries': 2,
                'nhsMHSRetryInterval': 'PT2S',
                'nhsMHsSN': 'urn:nhs:names:services:ebs',
                'nhsMhsSvcIA': 'urn:nhs:names:services:ebs:PRSC_IN070000UK08',
                'nhsMHSSyncReplyMode': 'None',
                'uniqueIdentifier': ['69720694737ed98c0242']
            }
        ]
        endpoints = EndpointCpm(incoming_json, filt)
        filtered_data = endpoints.filter_cpm_response()
        translated_data = endpoints.transform_to_ldap(filtered_data)
        self.assertEqual(translated_data, expected)
    
    def test_endpoint_process_success(self):
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("test_data", "cpm", RETURNED_ENDPOINTS_JSON))
        incoming_json = self._read_file(dir_path)
        filt = {
            "org_code": "RTX",
            "service_id": "urn:nhs:names:services:ebs:PRSC_IN070000UK08",
        }
        expected = [
            {
                'nhsIDCode': 'RTX',
                'nhsMHSAckRequested': 'always',
                'nhsMhsActor': ['urn:oasis:names:tc:ebxml-msg:actor:nextMSH'],
                'nhsMhsCPAId': '69720694737ed98c0242',
                'nhsMHSDuplicateElimination': 'always',
                'nhsMHSEndPoint': ['https://msg65-spine.msg.mpe.ncrs.nhs.uk/MHS/RTX/EBS3-5/messagehandler'],
                'nhsMhsFQDN': 'msg65-spine.msg.mpe.ncrs.nhs.uk',
                'nhsMHsIN': 'PRSC_IN070000UK08',
                'nhsMHSPartyKey': 'RTX-821088',
                'nhsMHSPersistDuration': 'PT4M',
                'nhsMHSRetries': 2,
                'nhsMHSRetryInterval': 'PT2S',
                'nhsMHsSN': 'urn:nhs:names:services:ebs',
                'nhsMhsSvcIA': 'urn:nhs:names:services:ebs:PRSC_IN070000UK08',
                'nhsMHSSyncReplyMode': 'None',
                'uniqueIdentifier': ['69720694737ed98c0242']
            }
        ]
        result = process_cpm_endpoint_request(incoming_json, filt)
        self.assertEqual(result, expected)

