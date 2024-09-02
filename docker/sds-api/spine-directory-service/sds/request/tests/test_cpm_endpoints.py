import json
import os
import requests
import tornado.web
import unittest

from unittest import TestCase
from unittest.mock import patch, call
from jsonschema import validate
from request.cpm import EndpointCpm, process_cpm_endpoint_request, CpmClient, get_endpoint_from_cpm, EndpointCpmClient, _extract_service_and_interaction
from request.base_handler import ORG_CODE_QUERY_PARAMETER_NAME, ORG_CODE_FHIR_IDENTIFIER, \
    IDENTIFIER_QUERY_PARAMETER_NAME, SERVICE_ID_FHIR_IDENTIFIER, PARTY_KEY_FHIR_IDENTIFIER
from lookup.sds_exception import SDSException

RETURNED_ENDPOINTS_JSON = "returned_endpoints_single.json"
RETURNED_ENDPOINTS_MULTIPLE_JSON = "returned_endpoints_multiple.json"
RETURNED_ENDPOINTS_CHANGE_JSON = "returned_endpoints_single_endpoint.json"

EXPECTED_LDAP_1 = {
    'nhsIDCode': 'D81631',
    'nhsMHSAckRequested': 'never',
    'nhsMhsActor': ['urn:oasis:names:tc:ebxml-msg:actor:nextMSH'],
    'nhsMhsCPAId': 'a83e020a3fe9c2988a36',
    'nhsMHSDuplicateElimination': 'never',
    'nhsMHSEndPoint': ['https://systmonespine1.tpp.nme.ncrs.nhs.uk/SystmOneMHS/NHSConnect/D81631/STU3/1'],
    'nhsMhsFQDN': 'systmonespine1.tpp.nme.ncrs.nhs.uk',
    'nhsMHsIN': 'fhir:rest:read:location-1',
    'nhsMHSPartyKey': 'D81631-827817',
    'nhsMHSPersistDuration': 'PT4M',
    'nhsMHSRetries': 2,
    'nhsMHSRetryInterval': 'PT2S',
    'nhsMHsSN': 'urn:nhs:names:services:gpconnect',
    'nhsMhsSvcIA': 'urn:nhs:names:services:gpconnect:fhir:rest:read:location-1',
    'nhsMHSSyncReplyMode': 'none',
    'uniqueIdentifier': ['a83e020a3fe9c2988a36']
}
EXPECTED_LDAP_2 = {
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
    'nhsMHSSyncReplyMode': 'none',
    'uniqueIdentifier': ['69720694737ed98c0242']
}
EXPECTED_LDAP_2_ENDPOINT_MODIFIED = {
    'nhsIDCode': 'RTX',
    'nhsMHSAckRequested': 'always',
    'nhsMhsActor': ['urn:oasis:names:tc:ebxml-msg:actor:nextMSH'],
    'nhsMhsCPAId': '69720694737ed98c0242',
    'nhsMHSDuplicateElimination': 'always',
    'nhsMHSEndPoint': ['https://msg.int.spine2.ncrs.nhs.uk/reliablemessaging/intermediary'],
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
EXPECTED_LDAP_3 = {
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
SPINE_CORE_ORG_CODE = "YES"

class TestCPMEndpoints(TestCase):
    
    @staticmethod
    def _read_file(file):
        with open(file, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def _set_core_spine_ods_code(mock_config, ods_code):
        def config_values(*args, **kwargs):
            return {
                "SPINE_CORE_ODS_CODE": ods_code
            }[args[0]]
        mock_config.side_effect = config_values
    
    @patch.dict(os.environ, {"USE_CPM": "1"})
    def test_filter_results_unsuccessful_missing_required_endpoint(self):
        org_code = f'{ORG_CODE_QUERY_PARAMETER_NAME}={ORG_CODE_FHIR_IDENTIFIER}|value'
        party_key = f'{IDENTIFIER_QUERY_PARAMETER_NAME}={PARTY_KEY_FHIR_IDENTIFIER}|value'
        service_id = f'{IDENTIFIER_QUERY_PARAMETER_NAME}={SERVICE_ID_FHIR_IDENTIFIER}|value'
        log_message=f"Missing or invalid query parameters. Should one of following combinations: ['{org_code}&{service_id}&{party_key}','{org_code}&{service_id}','{org_code}&{party_key}','{service_id}&{party_key}']"
        filters = [
            
            {
                "org_code": "",
                "interaction_id": "urn:nhs:names:services:ebs:PRSC_IN070000UK08",
            },
            {
                "org_code": "RTX",
                "interaction_id": "",
            },
            {
                "org_code": "",
                "party_key": "RTX-821088"
            },
            {
                "interaction_id": "",
                "party_key": "RTX-821088"
            },
            {
                "interaction_id": "urn:nhs:names:services:ebs:PRSC_IN070000UK08",
                "party_key": ""
            },
            {
                "org_code": "",
                "interaction_id": "",
            },
            {
                "org_code": "",
                "party_key": "",
            },
            {
                "interaction_id": "",
                "party_key": ""
            },
            {
            },
            {
                "interaction_id": "urn:nhs:names:services:ebs:PRSC_IN070000UK08",
            },
            {
                "org_code": "RTX",
            },
            {
                "party_key": "RTX-821088"
            },
            {
                "org_code": "",
                "interaction_id": "urn:nhs:names:services:ebs:PRSC_IN070000UK08",
                "party_key": ""
            },
            {
                "org_code": "RTX",
                "interaction_id": "",
                "party_key": ""
            },
            {
                "org_code": "",
                "interaction_id": "",
                "party_key": "RTX-821088"
            },
            {
                "org_code": "",
                "interaction_id": "",
                "party_key": ""
            }
        ]
        for filt in filters:
            with self.assertRaises(SDSException) as context:
                EndpointCpmClient(client_id="1234", apigee_url="https://foo.bar", query_params=filt)
            self.assertEqual(str(context.exception), log_message)
    
    @patch.dict(os.environ, {"USE_CPM": "1"})
    def test_filter_results_not_allowed(self):
        filters = [
            {
                "org_code": "RTX",
                "interaction_id": "urn:nhs:names:services:ebs:PRSC_IN070000UK08",
                "foo": "bar",
            },
            {
                "org_code": "RTX",
                "interaction_id": "urn:nhs:names:services:ebs:PRSC_IN070000UK08",
                "party_key": "RTX-821088",
                "foo": "bar",
            },
            {
                "interaction_id": "urn:nhs:names:services:ebs:PRSC_IN070000UK08",
                "party_key": "RTX-821088",
                "foo": "bar",
            },
            {
                "org_code": "RTX",
                "interaction_id": "urn:nhs:names:services:cpisquery:REPC_IN000007GB01",
                "foo": "bar",
            },
            {
                "org_code": "RTX",
                "interaction_id": "urn:nhs:names:services:cpisquery:REPC_IN000007GB01",
                "party_key": "RTX-821088",
                "foo": "bar",
            },
            {
                "interaction_id": "urn:nhs:names:services:cpisquery:REPC_IN000007GB01",
                "party_key": "RTX-821088",
                "foo": "bar",
            },
            {
                "interaction_id": "urn:nhs:names:services:cpisquery:REPC_IN000007GB01",
                "party_key": "RTX-821088",
                "manufacturing_organization": "LSP02",
            }
        ]
        for filt in filters:
            with self.assertRaises(SDSException) as context:
                EndpointCpmClient(client_id="1234", apigee_url="https://foo.bar", query_params=filt)
            if "manufacturing_organization" in filt:
                self.assertEqual(str(context.exception), "manufacturing_organization not allowed in filters")
            else:
                self.assertEqual(str(context.exception), "foo not allowed in filters")
    
    @patch.dict(os.environ, {"USE_CPM": "1"})
    def test_translated_endpoint_data(self):
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("test_data", "cpm", RETURNED_ENDPOINTS_JSON))
        incoming_json = self._read_file(dir_path)
        expected = [EXPECTED_LDAP_1]
        endpoints = EndpointCpm(incoming_json)
        translated_data = endpoints.transform_to_ldap()
        self.assertEqual(translated_data, expected)
    
    @patch.dict(os.environ, {"USE_CPM": "1"})
    def test_translated_endpoint_data_multiple_endpoints(self):
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("test_data", "cpm", RETURNED_ENDPOINTS_MULTIPLE_JSON))
        incoming_json = self._read_file(dir_path)
        expected = [
            EXPECTED_LDAP_1, 
            EXPECTED_LDAP_2
        ]
        endpoints = EndpointCpm(incoming_json)
        translated_data = endpoints.transform_to_ldap()
        assert len(translated_data) == 2
        self.assertEqual(translated_data, expected)
    
    @patch.dict(os.environ, {"USE_CPM": "1"})
    def test_endpoint_process_success(self):
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("test_data", "cpm", RETURNED_ENDPOINTS_JSON))
        incoming_json = self._read_file(dir_path)
        expected = [EXPECTED_LDAP_1]
        result = process_cpm_endpoint_request(incoming_json)
        self.assertEqual(result, expected)
    
    @patch.dict(os.environ, {"USE_CPM": "1"})
    def test_allowed_query_params(self):
        filters = [
            {
                "org_code": "RTX",
                "interaction_id": "urn:nhs:names:services:ebs:PRSC_IN070000UK08",
            },
            {
                "org_code": "RTX",
                "interaction_id": "urn:nhs:names:services:ebs:PRSC_IN070000UK08",
                "party_key": "RTX-821088"
            },
            {
                "interaction_id": "urn:nhs:names:services:ebs:PRSC_IN070000UK08",
                "party_key": "RTX-821088"
            },
            {
                "org_code": "RTX",
                "interaction_id": "urn:nhs:names:services:cpisquery:REPC_IN000007GB01",
            },
            {
                "org_code": "RTX",
                "interaction_id": "urn:nhs:names:services:cpisquery:REPC_IN000007GB01",
                "party_key": "RTX-821088"
            },
            {
                "interaction_id": "urn:nhs:names:services:cpisquery:REPC_IN000007GB01",
                "party_key": "RTX-821088"
            },
            {
                "org_code": " RTX",
                "interaction_id": " urn:nhs:names:services:cpisquery:REPC_IN000007GB01",
                "party_key": " RTX-821088"
            },
            {
                "org_code": "RTX ",
                "interaction_id": "urn:nhs:names:services:cpisquery:REPC_IN000007GB01 ",
                "party_key": "RTX-821088 "
            },
        ]
        for query in filters:
            cpm_client = EndpointCpmClient(client_id="1234", apigee_url="https://foo.bar", query_params=query)
            assert "org_code" not in cpm_client._params
            assert "interaction_id" not in cpm_client._params
            if "org_code" in query:
                assert "nhs_id_code" in cpm_client._params
                assert cpm_client._params["nhs_id_code"] == query["org_code"].strip()
            assert "nhs_mhs_svc_ia" in cpm_client._params
            assert cpm_client._params["nhs_mhs_svc_ia"] == query["interaction_id"].strip()
            if "party_key" in query:
                assert "party_key" not in cpm_client._params
                assert "nhs_mhs_party_key" in cpm_client._params
                assert cpm_client._params["nhs_mhs_party_key"] == query["party_key"].strip()
            assert isinstance(cpm_client, EndpointCpmClient)
    
    @patch.dict(os.environ, {"USE_CPM": "1"})
    def test_extract_service_interaction(self):
        test_data = [
            "foo:bar",
            "oof:foo:bar"
        ]
        for td in test_data:
            service, interaction =_extract_service_and_interaction(td)
            self.assertEqual(service, "foo")
            self.assertEqual(interaction, "bar")
        
        service = _extract_service_and_interaction(None)
        self.assertFalse(service)
    
    @patch.dict(os.environ, {"USE_CPM": "1"})
    @patch('utilities.config.get_config')
    def test_endpoint_process_success_reliability_not_applied(self, mock_config):
        self._set_core_spine_ods_code(mock_config, SPINE_CORE_ORG_CODE)
        dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.join("test_data", "cpm", RETURNED_ENDPOINTS_JSON))
        incoming_json = self._read_file(dir_path)
        expected = [EXPECTED_LDAP_1]
        result = process_cpm_endpoint_request(incoming_json)
        self.assertEqual(result, expected)


