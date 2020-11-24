import json
import unittest.mock
import uuid
from os import path

import fhirclient.models.endpoint as endpoint
import tornado.testing
import tornado.web

from request import routing_reliability_handler
from request.http_headers import HttpHeaders
from request.tests import test_request_handler
from utilities import message_utilities
from utilities import test_utilities

FILE_PATH_JSON = path.join(path.dirname(__file__), "examples/routing_reliability_result.json")
FIXED_UUID = "f0f0e921-92ca-4a88-a550-2dbb36f703af"
ROUTING_AND_RELIABILITY_DETAILS = {
    "nhsMHSEndPoint": [
        "https://192.168.128.11/sync-service"
    ],
    "nhsMHSPartyKey": "YES-0000806",
    "nhsMhsCPAId": "S20001A000168",
    "nhsMhsFQDN": "192.168.128.11",
    "uniqueIdentifier": [
        "928942012545"
    ],
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
        self.routing.get_routing_and_reliability.return_value = test_utilities.awaitable(ROUTING_AND_RELIABILITY_DETAILS)

        response = self.fetch(test_request_handler.build_url(), method="GET")
        json_body = json.loads(response.body)
        expected = open(FILE_PATH_JSON, "r").read()
        json_with_fixed_uuid = message_utilities.replace_uuid(json.dumps(json_body, indent=2), FIXED_UUID)

        self.endpoint_resource_validation(json_body)
        self.assertEqual(response.code, 200)
        self.assertEqual(expected, json_with_fixed_uuid)
        self.assertEqual(response.headers.get(HttpHeaders.CONTENT_TYPE, None), "application/fhir+json")
        self.routing.get_routing_and_reliability.assert_called_with(test_request_handler.ORG_CODE, test_request_handler.SERVICE_ID)

    def test_correlation_id_is_set_as_response_header(self):
        with self.subTest("X-Correlation-ID is set on 200 response"):
            correlation_id = str(uuid.uuid4()).upper()
            self.routing.get_routing_and_reliability.return_value = test_utilities.awaitable(ROUTING_AND_RELIABILITY_DETAILS)
            response = self.fetch(test_request_handler.build_url(),
                                  method="GET", headers={'X-Correlation-ID': correlation_id})
            self.assertEqual(response.code, 200)
            self.assertEqual(response.headers.get('X-Correlation-ID'), correlation_id)

        with self.subTest("X-Correlation-ID is set on 500 response"):
            correlation_id = str(uuid.uuid4()).upper()
            self.routing.get_routing_and_reliability.side_effect = Exception
            response = self.fetch(test_request_handler.build_url(),
                                  method="GET", headers={'X-Correlation-ID': correlation_id})
            self.assertEqual(response.code, 500)
            self.assertEqual(response.headers.get('X-Correlation-ID'), correlation_id)

        with self.subTest("X-Correlation-ID is set on 400 response"):
            correlation_id = str(uuid.uuid4()).upper()
            response = self.fetch(
                test_request_handler.build_url(org_code=None, service_id=test_request_handler.SERVICE_ID),
                method="GET", headers={'X-Correlation-ID': correlation_id})
            self.assertEqual(response.code, 400)
            self.assertEqual(response.headers.get('X-Correlation-ID'), correlation_id)

    def test_get_returns_error(self):
        with self.subTest("Routing and reliability lookup error"):
            self.routing.get_routing_and_reliability.side_effect = Exception

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
            self.routing.get_routing_and_reliability.return_value = test_utilities.awaitable(ROUTING_AND_RELIABILITY_DETAILS)
            response = self.fetch(test_request_handler.build_url(), method="GET")

            json_body = json.loads(response.body)
            expected = open(FILE_PATH_JSON, "r").read()
            json_with_fixed_uuid = message_utilities.replace_uuid(json.dumps(json_body, indent=2), FIXED_UUID)

            self.assertEqual(response.code, 200)
            self.assertEqual(expected, json_with_fixed_uuid)
            self.assertEqual(response.headers.get(HttpHeaders.CONTENT_TYPE, None), "application/fhir+json")

        with self.subTest("Accept header is case-insensitive application/fhir+json"):
            headers = {'Accept': 'application/fhir+JSON'}
            self.routing.get_routing_and_reliability.return_value = test_utilities.awaitable(ROUTING_AND_RELIABILITY_DETAILS)
            response = self.fetch(test_request_handler.build_url(), method="GET", headers=headers)

            json_body = json.loads(response.body)
            expected = open(FILE_PATH_JSON, "r").read()
            json_with_fixed_uuid = message_utilities.replace_uuid(json.dumps(json_body, indent=2), FIXED_UUID)

            self.assertEqual(response.code, 200)
            self.assertEqual(expected, json_with_fixed_uuid)
            self.assertEqual(response.headers.get(HttpHeaders.CONTENT_TYPE, None), "application/fhir+json")

        with self.subTest("Accept header is invalid"):
            headers = {'Accept': 'invalid-header'}
            self.routing.get_routing_and_reliability.return_value = test_utilities.awaitable(ROUTING_AND_RELIABILITY_DETAILS)
            response = self.fetch(test_request_handler.build_url(), method="GET", headers=headers)

            self.assertEqual(response.code, 406)

    @staticmethod
    def endpoint_resource_validation(json_body: dict):
        endpoint.Endpoint(json_body)
