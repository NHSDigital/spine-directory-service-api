import json
import os
import re
import unittest

from utilities.SdsHttpRequestBuilder import SdsHttpRequestBuilder

TEST_DATA_BASE_PATH = os.path.join(os.path.dirname(__file__), '../tests/test_data/')


def read_test_data_json(file):
    with open(os.path.join(TEST_DATA_BASE_PATH, file)) as json_file:
        return json.load(json_file)


def test_should_return_successful_response(test_data_file_name, request_builder_modifier=None):
    assertions = unittest.TestCase('__init__')

    request_builder = SdsHttpRequestBuilder()
    if request_builder_modifier is not None:
        request_builder_modifier(request_builder)

    response = request_builder \
        .with_org_code('YES') \
        .with_service_id('urn:nhs:names:services:psis:REPC_IN150016UK05') \
        .execute_get_expecting_success()

    assertions.assertEqual('application/fhir+json', response.headers['Content-Type'])

    expected_body = read_test_data_json(test_data_file_name)
    body = json.loads(response.content.decode('UTF-8'))

    # id is generated so we first check if existing one is an UUID
    # and then we use it in the expected json
    actual_id = body['id']
    uuid4hex = re.compile('^[A-F0-9]{8}-?[A-F0-9]{4}-?[A-F0-9]{4}-?[A-F0-9]{4}-?[A-F0-9]{12}')
    assertions.assertTrue(bool(uuid4hex.match(actual_id)))

    expected_body['id'] = actual_id

    assertions.assertEqual(expected_body, body)


def test_should_return_bad_request_when_query_parameters_are_missing():
    SdsHttpRequestBuilder() \
        .execute_get_expecting_bad_request_response()

    SdsHttpRequestBuilder() \
        .with_org_code('YES') \
        .execute_get_expecting_bad_request_response()

    SdsHttpRequestBuilder() \
        .with_service_id('urn:nhs:names:services:psis:REPC_IN150016UK05') \
        .execute_get_expecting_bad_request_response()


def test_endpoint_should_be_case_insensitive(test_data_file_name):
    def modify_request_builder(request_builder):
        request_builder.sds_host = request_builder.sds_host.upper()

    test_should_return_successful_response(test_data_file_name, modify_request_builder)
