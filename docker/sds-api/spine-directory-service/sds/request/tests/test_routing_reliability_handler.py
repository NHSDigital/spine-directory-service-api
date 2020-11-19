from os import path
from request.tests.request_handler_test_base import RequestHandlerTestBase, ORG_CODE, SERVICE_ID, PARTY_KEY
from utilities import test_utilities

EXPECTED_ENDPOINT_JSON_FILE_PATH = path.join(path.dirname(__file__), "examples/endpoint.json")
ROUTING_AND_RELIABILITY_DETAILS = [{
    "nhsMHSEndPoint": [
        "https://192.168.128.11/sync-service"
    ],
    "nhsMHSPartyKey": "YES-0000806",
    "nhsMhsCPAId": "S20001A000168",
    "nhsMhsFQDN": "192.168.128.11",
    "uniqueIdentifier": [
        "928942012545"
    ],
    "nhsMHSAckRequested": "never",
    "nhsMHSDuplicateElimination": "never",
    "nhsMHSPersistDuration": [],
    "nhsMHSRetries": [],
    "nhsMHSRetryInterval": [],
    "nhsMHSSyncReplyMode": "None"
}]


class TestRoutingReliabilityRequestHandler(RequestHandlerTestBase):

    def test_get(self):
        self.sds_client.get_mhs_details.return_value = test_utilities.awaitable(ROUTING_AND_RELIABILITY_DETAILS)

        super()._test_get(super()._build_endpoint_url(), EXPECTED_ENDPOINT_JSON_FILE_PATH)

        self.sds_client.get_mhs_details.assert_called_with(ORG_CODE, SERVICE_ID, PARTY_KEY)

    def test_correlation_id_is_set_as_response_header(self):
        def mock200():
            self.sds_client.get_mhs_details.return_value = test_utilities.awaitable(ROUTING_AND_RELIABILITY_DETAILS)

        def mock500():
            self.sds_client.get_mhs_details.side_effect = Exception

        super()._test_correlation_id_is_set_as_response_header(
            self._build_endpoint_url(),
            self._build_endpoint_url(org_code=None, service_id=SERVICE_ID, party_key=PARTY_KEY),
            mock200,
            mock500
        )

    def test_get_returns_error(self):
        with self.subTest("Lookup error"):
            self.sds_client.get_mhs_details.side_effect = Exception
            response = self.fetch(self._build_endpoint_url(), method="GET")
            self.assertEqual(response.code, 500)

    def test_get_handles_missing_params(self):
        with self.subTest("Missing Org Code"):
            response = self.fetch(self._build_endpoint_url(org_code=None, service_id=SERVICE_ID), method="GET")
            self.assertEqual(response.code, 400)

        with self.subTest("Missing Service ID and party key"):
            response = self.fetch(self._build_endpoint_url(org_code=ORG_CODE, service_id=None, party_key=None), method="GET")
            self.assertEqual(response.code, 400)

    def test_get_handles_different_accept_header(self):
        self.sds_client.get_mhs_details.return_value = test_utilities.awaitable(ROUTING_AND_RELIABILITY_DETAILS)
        super()._test_get_handles_different_accept_header(super()._build_endpoint_url(), EXPECTED_ENDPOINT_JSON_FILE_PATH)
