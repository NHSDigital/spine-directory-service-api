import json
import unittest.mock

import tornado.testing
import tornado.web

from request import routing_reliability_handler
from request.http_headers import HttpHeaders
from request.tests import test_request_handler
from utilities import test_utilities

END_POINT_DETAILS = {
    "nhsMHSEndPoint": [
        "https://192.168.128.11/sync-service"
    ],
    "nhsMHSPartyKey": "YES-0000806",
    "nhsMhsCPAId": "S20001A000168",
    "nhsMhsFQDN": "192.168.128.11",
    "uniqueIdentifier": [
        "928942012545"
    ]
}

RELIABILITY_DETAILS = {
    "nhsMHSAckRequested": "never",
    "nhsMHSDuplicateElimination": "never",
    "nhsMHSPersistDuration": [],
    "nhsMHSRetries": [],
    "nhsMHSRetryInterval": [],
    "nhsMHSSyncReplyMode": "None"
}

COMBINED_DETAILS = {
    "nhsMHSAckRequested": "never",
    "nhsMHSDuplicateElimination": "never",
    "nhsMHSEndPoint": [
        "https://192.168.128.11/sync-service"
    ],
    "nhsMHSPartyKey": "YES-0000806",
    "nhsMHSPersistDuration": [],
    "nhsMHSRetries": [],
    "nhsMHSRetryInterval": [],
    "nhsMHSSyncReplyMode": "None",
    "nhsMhsCPAId": "S20001A000168",
    "nhsMhsFQDN": "192.168.128.11",
    "uniqueIdentifier": [
        "928942012545"
    ]
}


class TestRoutingReliabilityRequestHandler(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        self.routing = unittest.mock.Mock()

        return tornado.web.Application([
            (r"/", routing_reliability_handler.RoutingReliabilityRequestHandler, {"routing": self.routing})
        ])

    def test_get(self):
        self.routing.get_end_point.return_value = test_utilities.awaitable(END_POINT_DETAILS)
        self.routing.get_reliability.return_value = test_utilities.awaitable(RELIABILITY_DETAILS)

        response = self.fetch(test_request_handler.build_url(), method="GET")

        self.assertEqual(response.code, 200)
        self.assertEqual(COMBINED_DETAILS, json.loads(response.body))
        self.assertEqual(response.headers.get(HttpHeaders.CONTENT_TYPE, None), "application/json")
        self.routing.get_end_point.assert_called_with(test_request_handler.ORG_CODE, test_request_handler.SERVICE_ID)
        self.routing.get_reliability.assert_called_with(test_request_handler.ORG_CODE, test_request_handler.SERVICE_ID)

    def test_get_returns_error(self):
        with self.subTest("Routing lookup error"):
            self.routing.get_end_point.side_effect = Exception

            response = self.fetch(test_request_handler.build_url(), method="GET")

            self.assertEqual(response.code, 500)

        with self.subTest("Reliability lookup error"):
            self.routing.get_reliability.side_effect = Exception

            response = self.fetch(test_request_handler.build_url(), method="GET")

            self.assertEqual(response.code, 500)

    def test_get_handles_missing_params(self):
        with self.subTest("Missing Org Code"):
            response = self.fetch(
                test_request_handler.build_url(org_code=None, service_id=test_request_handler.SERVICE_ID), method="GET")

            self.assertEqual(response.code, 400)

        with self.subTest("Missing Service ID"):
            response = self.fetch(
                test_request_handler.build_url(org_code=test_request_handler.ORG_CODE, service_id=None), method="GET")

            self.assertEqual(response.code, 400)

        with self.subTest("Missing Org Code & Service ID"):
            response = self.fetch(test_request_handler.build_url(org_code=None, service_id=None), method="GET")

            self.assertEqual(response.code, 400)

    def test_get_handles_different_accept_header(self):
        with self.subTest("Accept header is missing"):
            self.routing.get_end_point.return_value = test_utilities.awaitable(END_POINT_DETAILS)
            self.routing.get_reliability.return_value = test_utilities.awaitable(RELIABILITY_DETAILS)
            response = self.fetch(test_request_handler.build_url(), method="GET")

            self.assertEqual(response.code, 200)
            self.assertEqual(response.headers.get(HttpHeaders.CONTENT_TYPE, None), "application/json")

        with self.subTest("Accept header is application/fhir+json"):
            headers = {'Accept': 'application/fhir+json'}
            self.routing.get_end_point.return_value = test_utilities.awaitable(END_POINT_DETAILS)
            self.routing.get_reliability.return_value = test_utilities.awaitable(RELIABILITY_DETAILS)
            response = self.fetch(test_request_handler.build_url(), method="GET", headers=headers)

            self.assertEqual(response.code, 200)
            self.assertEqual(response.headers.get(HttpHeaders.CONTENT_TYPE, None), "application/fhir+json")

        with self.subTest("Accept header is application/fhir+xml"):
            headers = {'Accept': 'application/fhir+xml'}
            self.routing.get_end_point.return_value = test_utilities.awaitable(END_POINT_DETAILS)
            self.routing.get_reliability.return_value = test_utilities.awaitable(RELIABILITY_DETAILS)
            response = self.fetch(test_request_handler.build_url(), method="GET", headers=headers)

            self.assertEqual(response.code, 200)
            self.assertEqual(response.headers.get(HttpHeaders.CONTENT_TYPE, None), "application/fhir+xml")

        with self.subTest("Accept header is invalid"):
            headers = {'Accept': 'invalid-header'}
            self.routing.get_end_point.return_value = test_utilities.awaitable(END_POINT_DETAILS)
            self.routing.get_reliability.return_value = test_utilities.awaitable(RELIABILITY_DETAILS)
            response = self.fetch(test_request_handler.build_url(), method="GET", headers=headers)

            self.assertEqual(response.code, 400)
