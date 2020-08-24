import json
import unittest.mock

import fhirclient.models.endpoint as endpoint
import lxml
import tornado.testing
import tornado.web
from lxml import etree

from request import routing_reliability_handler
from request.http_headers import HttpHeaders
from request.tests import test_request_handler
from utilities import message_utilities
from utilities import test_utilities

FIXED_UUID = "f0f0e921-92ca-4a88-a550-2dbb36f703af"
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
        json_body = json.loads(response.body)
        expected = open("examples/routing_reliability_result.json", "r").read()
        json_with_fixed_uuid = message_utilities.replace_uuid(json.dumps(json_body, indent=2), FIXED_UUID)

        self.endpoint_resource_validation(json_body)
        self.assertEqual(response.code, 200)
        self.assertEqual(expected, json_with_fixed_uuid)
        self.assertEqual(response.headers.get(HttpHeaders.CONTENT_TYPE, None), "application/fhir+json")
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

            json_body = json.loads(response.body)
            expected = open("examples/routing_reliability_result.json", "r").read()
            json_with_fixed_uuid = message_utilities.replace_uuid(json.dumps(json_body, indent=2), FIXED_UUID)

            self.assertEqual(response.code, 200)
            self.assertEqual(expected, json_with_fixed_uuid)
            self.assertEqual(response.headers.get(HttpHeaders.CONTENT_TYPE, None), "application/fhir+json")

        with self.subTest("Accept header is case-insensitive application/fhir+json"):
            headers = {'Accept': 'application/fhir+JSON'}
            self.routing.get_end_point.return_value = test_utilities.awaitable(END_POINT_DETAILS)
            self.routing.get_reliability.return_value = test_utilities.awaitable(RELIABILITY_DETAILS)
            response = self.fetch(test_request_handler.build_url(), method="GET", headers=headers)

            json_body = json.loads(response.body)
            expected = open("examples/routing_reliability_result.json", "r").read()
            json_with_fixed_uuid = message_utilities.replace_uuid(json.dumps(json_body, indent=2), FIXED_UUID)

            self.assertEqual(response.code, 200)
            self.assertEqual(expected, json_with_fixed_uuid)
            self.assertEqual(response.headers.get(HttpHeaders.CONTENT_TYPE, None), "application/fhir+json")

        with self.subTest("Accept header is application/fhir+xml"):
            headers = {'Accept': 'application/fhir+xml'}
            self.routing.get_end_point.return_value = test_utilities.awaitable(END_POINT_DETAILS)
            self.routing.get_reliability.return_value = test_utilities.awaitable(RELIABILITY_DETAILS)
            response = self.fetch(test_request_handler.build_url(), method="GET", headers=headers)

            body_with_fixed_uuid = message_utilities.replace_uuid(response.body.decode(), FIXED_UUID)
            body_xml = etree.tostring(lxml.etree.fromstring(body_with_fixed_uuid))
            expected = etree.tostring(etree.parse("examples/routing_reliability_result.xml"))

            self.assertEqual(response.code, 200)
            self.assertEqual(expected, body_xml)
            self.assertEqual(response.headers.get(HttpHeaders.CONTENT_TYPE, None), "application/fhir+xml")

        with self.subTest("Accept header is invalid"):
            headers = {'Accept': 'invalid-header'}
            self.routing.get_end_point.return_value = test_utilities.awaitable(END_POINT_DETAILS)
            self.routing.get_reliability.return_value = test_utilities.awaitable(RELIABILITY_DETAILS)
            response = self.fetch(test_request_handler.build_url(), method="GET", headers=headers)

            self.assertEqual(response.code, 400)

    def endpoint_resource_validation(self, json_body: dict):
        endpoint.Endpoint(json_body)
