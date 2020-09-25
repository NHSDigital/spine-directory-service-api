from unittest import TestCase

from utilities.TestUtils import \
    test_should_return_successful_response, \
    test_should_return_bad_request_when_query_parameters_are_missing, \
    test_endpoint_should_be_case_insensitive


class RoutingAndReliabilityHandlerTests(TestCase):

    def test_should_return_successful_response(self):
        test_should_return_successful_response("routing_reliability_response.json")

    def test_should_return_bad_request_when_query_parameters_are_missing(self):
        test_should_return_bad_request_when_query_parameters_are_missing()

    def test_endpoint_should_be_case_insensitive(self):
        test_endpoint_should_be_case_insensitive("routing_reliability_response.json")
