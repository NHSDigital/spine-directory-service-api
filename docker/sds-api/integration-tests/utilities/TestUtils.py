import json
import os
import unittest

from utilities.SdsHttpRequestBuilder import SdsHttpRequestBuilder

TEST_DATA_BASE_PATH = os.path.join(os.path.dirname(__file__), '../tests/test_data/')


def read_test_data_json(file):
    with open(os.path.join(TEST_DATA_BASE_PATH, file)) as json_file:
        return json.load(json_file)


def test_should_return_successful_response(test_data_file_name):
    assertions = unittest.TestCase('__init__')

    response = SdsHttpRequestBuilder() \
        .with_org_code('YES') \
        .with_service_id('urn:nhs:names:services:psis:REPC_IN150016UK05') \
        .execute_get_expecting_success()

    assertions.assertEqual('application/json', response.headers['Content-Type'])

    expected_body = read_test_data_json(test_data_file_name)
    body = json.loads(response.content.decode('UTF-8'))
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
