from os import path
from request.tests.request_handler_test_base import RequestHandlerTestBase, ORG_CODE, SERVICE_ID, PARTY_KEY, MANAGING_ORG
from utilities import test_utilities

EXPECTED_DEVICE_JSON_FILE_PATH = path.join(path.dirname(__file__), "examples/device.json")
ACCREDITED_SYSTEM_DETAILS = [{
    "nhsMHSPartyKey": "YES-0000806",
    "nhsMhsCPAId": "S20001A000168",
    "uniqueIdentifier": [
        "928942012545"
    ]
}]


class TestAccreditedSystemHandler(RequestHandlerTestBase):

    def test_get(self):
        self.sds_client.get_as_details.return_value = test_utilities.awaitable(ACCREDITED_SYSTEM_DETAILS)

        super()._test_get(super()._build_device_url(), EXPECTED_DEVICE_JSON_FILE_PATH)

        self.sds_client.get_as_details.assert_called_with(ORG_CODE, SERVICE_ID, MANAGING_ORG, PARTY_KEY)

    def test_correlation_id_is_set_as_response_header(self):
        def mock200():
            self.sds_client.get_as_details.return_value = test_utilities.awaitable(ACCREDITED_SYSTEM_DETAILS)

        def mock500():
            self.sds_client.get_as_details.side_effect = Exception

        super()._test_correlation_id_is_set_as_response_header(
            self._build_device_url(),
            self._build_device_url(org_code=None),
            mock200,
            mock500
        )

    def test_get_returns_error(self):
        with self.subTest("Lookup error"):
            self.sds_client.get_as_details.side_effect = Exception
            response = self.fetch(self._build_device_url(), method="GET")
            self.assertEqual(response.code, 500)

    def test_get_handles_missing_params(self):
        with self.subTest("Missing Org Code"):
            response = self.fetch(self._build_device_url(org_code=None), method="GET")
            self.assertEqual(response.code, 400)

        with self.subTest("Missing Service ID and party key"):
            response = self.fetch(self._build_device_url(org_code=ORG_CODE, service_id=None, party_key=None), method="GET")
            self.assertEqual(response.code, 400)

    def test_get_handles_different_accept_header(self):
        self.sds_client.get_as_details.return_value = test_utilities.awaitable(ACCREDITED_SYSTEM_DETAILS)
        super()._test_get_handles_different_accept_header(super()._build_device_url(), EXPECTED_DEVICE_JSON_FILE_PATH)
