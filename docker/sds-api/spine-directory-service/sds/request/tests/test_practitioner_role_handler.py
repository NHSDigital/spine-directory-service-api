from os import path
from request.tests.request_handler_test_base import RequestHandlerTestBase, USER_ROLE_CODE
from utilities import test_utilities

EXPECTED_SINGLE_PRACTITIONER_ROLE_JSON_FILE_PATH = path.join(path.dirname(__file__), "examples/single_practitioner_role.json")
# LDAP RESULT
SINGLE_PRACTITIONER_ROLE_DETAILS = [{
    "nhsJobRoleCode": ["S0010:G0020:R0050"],
    "uniqueIdentifier": [
        "928942012545"
    ]
}]


class TestPractitionerRoleHandler(RequestHandlerTestBase):

    def test_get_single_result(self):
        self.sds_client.get_practitioner_role_details.return_value = test_utilities.awaitable(SINGLE_PRACTITIONER_ROLE_DETAILS)

        super()._test_get(
            super()._build_pr_url(user_role_id=USER_ROLE_CODE),
            EXPECTED_SINGLE_PRACTITIONER_ROLE_JSON_FILE_PATH)

    def test_correlation_id_is_set_as_response_header(self):
        def mock200():
            self.sds_client.get_practitioner_role_details.return_value = test_utilities.awaitable(SINGLE_PRACTITIONER_ROLE_DETAILS)

        def mock500():
            self.sds_client.get_practitioner_role_details.side_effect = Exception

        super()._test_correlation_id_is_set_as_response_header(
            self._build_pr_url(),
            self._build_pr_url(user_role_id=None),
            mock200,
            mock500
        )

    def test_get_returns_error(self):
        with self.subTest("Lookup error"):
            self.sds_client.get_practitioner_role_details.side_effect = Exception("some error")
            response = self.fetch(self._build_pr_url(), method="GET")
            self.assertEqual(response.code, 500)
            super()._assert_500_operation_outcome(response.body.decode())

    def test_get_handles_missing_params(self):
        with self.subTest("Missing Role Code"):
            response = self.fetch(self._build_pr_url(user_role_id=None), method="GET")
            self.assertEqual(response.code, 400)
            super()._assert_400_operation_outcome(
                response.body.decode(),
                "HTTP 400: Bad Request (Missing or invalid 'user-role-id' query parameter. Should be 'user-role-id=https://fhir.nhs.uk/Id/nhsJobRoleCode|value')")

        with self.subTest("Empty Role Code"):
            response = self.fetch(self._build_pr_url(user_role_id=""), method="GET")
            self.assertEqual(response.code, 400)
            super()._assert_400_operation_outcome(
                response.body.decode(),
                "HTTP 400: Bad Request (Missing or invalid 'user-role-id' query parameter. Should be 'user-role-id=https://fhir.nhs.uk/Id/nhsJobRoleCode|value')")

        with self.subTest("Role Code is not digits"):
            response = self.fetch(self._build_pr_url(user_role_id="abc"), method="GET")
            self.assertEqual(response.code, 400)
            super()._assert_400_operation_outcome(
                response.body.decode(),
                "HTTP 400: Bad Request (Invalid 'user-role-id' query value. Should be 'user-role-id=https://fhir.nhs.uk/Id/nhsJobRoleCode|value' where value is a digit.)")
