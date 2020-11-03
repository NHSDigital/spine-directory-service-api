from unittest import TestCase

from utilities.TestUtils import \
    test_should_return_successful_response, \
    test_should_return_400_when_query_parameters_are_missing, \
    test_endpoint_should_be_case_insensitive, test_should_return_405_when_using_post, \
    test_should_return_404_when_calling_invalid_endpoint


class RoutingAndReliabilityHandlerTests(TestCase):

    def test_should_return_successful_response(self):
        test_should_return_successful_response("routing_reliability_response.json")

    def test_endpoint_should_be_case_insensitive(self):
        test_endpoint_should_be_case_insensitive("routing_reliability_response.json")

    def test_should_return_400_when_query_parameters_are_missing(self):
        test_should_return_400_when_query_parameters_are_missing()

    def test_should_return_404_when_calling_invalid_endpoint(self):
        test_should_return_404_when_calling_invalid_endpoint()

    def test_should_return_405_when_using_POST(self):
        test_should_return_405_when_using_post()
