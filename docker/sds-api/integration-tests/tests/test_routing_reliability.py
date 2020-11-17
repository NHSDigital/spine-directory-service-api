import json
import re
from unittest import TestCase

from utilities.SdsHttpRequestBuilder import SdsHttpRequestBuilder
from utilities.TestUtils import read_test_data_json, assert_400_operation_outcome, assert_405_operation_outcome, \
    assert_404_operation_outcome


class RoutingAndReliabilityHandlerTests(TestCase):

    def test_should_return_successful_response(self, request_builder_modifier=None):
        request_builder = SdsHttpRequestBuilder()
        if request_builder_modifier is not None:
            request_builder_modifier(request_builder)

        response = request_builder \
            .with_org_code('YES') \
            .with_service_id('urn:nhs:names:services:psis:REPC_IN150016UK05') \
            .with_party_key('YES-0000806') \
            .execute_get_expecting_success()

        self.assertEqual('application/fhir+json', response.headers['Content-Type'])

        expected_body = read_test_data_json("routing_reliability_response.json")
        body = json.loads(response.content.decode('UTF-8'))

        # id is generated so we first check if existing one is an UUID
        # and then we use it in the expected json
        current_id = body['id']
        current_link_url = body['link'][0]['url']
        current_entry_full_url = body["entry"][0]["fullUrl"]
        current_resource_id = body["entry"][0]["resource"]["id"]

        uuidRegex = re.compile('^[A-F0-9]{8}-?[A-F0-9]{4}-?[A-F0-9]{4}-?[A-F0-9]{4}-?[A-F0-9]{12}')
        self.assertTrue(bool(uuidRegex.match(current_id)))
        self.assertTrue(bool(uuidRegex.match(current_resource_id)))
        fullUrlRegex = re.compile('^(http:\/\/localhost:9000\/(endpoint|ENDPOINT)\/)([A-F0-9]{8}-?[A-F0-9]{4}-?[A-F0-9]{4}-?[A-F0-9]{4}-?[A-F0-9]{12})')
        self.assertTrue(bool(fullUrlRegex.match(current_entry_full_url)))

        expected_body['id'] = current_id
        expected_body["entry"][0]["fullUrl"] = current_entry_full_url
        expected_body["entry"][0]["resource"]["id"] = current_resource_id
        expected_body['link'][0]['url'] = current_link_url

        self.assertEqual(expected_body, body)

    def test_should_return_successful_response_when_there_are_no_results(self):
        response = SdsHttpRequestBuilder()\
            .with_org_code('YES') \
            .with_service_id('non-existing') \
            .execute_get_expecting_success()

        self.assertEqual('application/fhir+json', response.headers['Content-Type'])

        body = json.loads(response.content.decode('UTF-8'))

        self.assertEqual(body["total"], 0)
        self.assertEqual(len(body["entry"]), 0)

    def test_should_return_400_when_query_parameters_are_missing(self):
        # all missing
        response = SdsHttpRequestBuilder() \
            .execute_get_expecting_bad_request_response()
        assert_400_operation_outcome(response.content, "HTTP 400: Bad Request (Missing argument organization)")

        # empty org code
        response = SdsHttpRequestBuilder() \
            .with_org_code('') \
            .with_service_id('') \
            .with_party_key('') \
            .execute_get_expecting_bad_request_response()
        assert_400_operation_outcome(response.content, "HTTP 400: Missing or invalid 'organization' query parameter. Should be 'organization=https://fhir.nhs.uk/Id/ods-organization-code|value'")

        # invalid fhir code for org code
        response = SdsHttpRequestBuilder() \
            .with_org_code('YES', fhir_code="something_else") \
            .with_service_id('urn:nhs:names:services:psis:REPC_IN150016UK05') \
            .execute_get_expecting_bad_request_response()
        assert_400_operation_outcome(response.content, "HTTP 400: Missing or invalid 'organization' query parameter. Should be 'organization=https://fhir.nhs.uk/Id/ods-organization-code|value'")

        # missing service id
        response = SdsHttpRequestBuilder() \
            .with_org_code('YES') \
            .execute_get_expecting_bad_request_response()
        assert_400_operation_outcome(response.content, "HTTP 400: Missing or invalid 'identifier' query parameter. Should be 'identifier=https://fhir.nhs.uk/Id/nhsEndpointServiceId|value'or 'identifier=https://fhir.nhs.uk/Id/nhsMhsPartyKey|value'")

        # empty service id
        response = SdsHttpRequestBuilder() \
            .with_org_code('YES') \
            .with_service_id('') \
            .execute_get_expecting_bad_request_response()
        assert_400_operation_outcome(response.content, "HTTP 400: Missing or invalid 'identifier' query parameter. Should be 'identifier=https://fhir.nhs.uk/Id/nhsEndpointServiceId|value'or 'identifier=https://fhir.nhs.uk/Id/nhsMhsPartyKey|value'")

        # invalid fhir code for service id
        response = SdsHttpRequestBuilder() \
            .with_org_code('YES') \
            .with_service_id('urn:nhs:names:services:psis:REPC_IN150016UK05', fhir_code="something_else") \
            .execute_get_expecting_bad_request_response()
        assert_400_operation_outcome(response.content, "HTTP 400: Missing or invalid 'identifier' query parameter. Should be 'identifier=https://fhir.nhs.uk/Id/nhsEndpointServiceId|value'or 'identifier=https://fhir.nhs.uk/Id/nhsMhsPartyKey|value'")

    def test_should_return_405_when_using_post(self):
        response = SdsHttpRequestBuilder() \
            .with_method("POST") \
            .with_org_code('YES') \
            .with_service_id('urn:nhs:names:services:psis:REPC_IN150016UK05') \
            .execute()

        self.assertEqual(response.status_code, 405)
        assert_405_operation_outcome(response.content)

    def test_should_return_404_when_calling_invalid_endpoint(self):
        response = SdsHttpRequestBuilder() \
            .with_custom_endpoint("something") \
            .with_org_code('YES') \
            .with_service_id('urn:nhs:names:services:psis:REPC_IN150016UK05') \
            .execute()

        self.assertEqual(response.status_code, 404)
        assert_404_operation_outcome(response.content)

    def test_endpoint_should_be_case_insensitive(self):
        def modify_request_builder(request_builder):
            request_builder.sds_host = request_builder.sds_host.upper()

        self.test_should_return_successful_response(modify_request_builder)
