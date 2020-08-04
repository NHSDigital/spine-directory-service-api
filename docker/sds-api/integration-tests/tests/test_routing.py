from unittest import TestCase

from utilities.TestUtils import test_should_return_successful_response, \
    test_should_return_bad_request_when_query_parameters_are_missing


class RoutingHandlerTests(TestCase):

    def test_should_return_successful_response(self):
        test_should_return_successful_response("routing", "routing_response.json")

    def test_should_return_bad_request_when_query_parameters_are_missing(self):
        test_should_return_bad_request_when_query_parameters_are_missing("routing")