import json
import unittest.mock
import uuid
from abc import ABC
from typing import Optional

import tornado.testing
import tornado.web

from request import routing_reliability_handler, accredited_system_handler
from request.http_headers import HttpHeaders
from utilities import message_utilities

ORG_CODE = "org"
SERVICE_ID = "service"
PARTY_KEY = "some_party_key"
MANAGING_ORG = "some_manufacturer"
FIXED_UUID = "f0f0e921-92ca-4a88-a550-2dbb36f703af"


class RequestHandlerTestBase(ABC, tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        self.sds_client = unittest.mock.Mock()

        return tornado.web.Application([
            (r"/endpoint", routing_reliability_handler.RoutingReliabilityRequestHandler, {"sds_client": self.sds_client}),
            (r"/device", accredited_system_handler.AccreditedSystemRequestHandler, {"sds_client": self.sds_client})
        ])

    def _test_get(self, url, expected_json_file_path):
        response = self.fetch(url, method="GET")

        current, expected = self._get_current_and_expected_body(response, expected_json_file_path)

        self.assertEqual(response.code, 200)
        self.assertEqual(expected, current)
        self.assertEqual(response.headers.get(HttpHeaders.CONTENT_TYPE, None), "application/fhir+json")
        self.assertIsNotNone(response.headers.get(HttpHeaders.X_CORRELATION_ID, None))

    def _test_correlation_id_is_set_as_response_header(self, url, invalid_url, mock_200, mock_500):
        with self.subTest("X-Correlation-ID is set on 200 response"):
            correlation_id = str(uuid.uuid4()).upper()
            mock_200()
            response = self.fetch(url, method="GET", headers={'X-Correlation-ID': correlation_id})
            self.assertEqual(response.code, 200)
            self.assertEqual(response.headers.get('X-Correlation-ID'), correlation_id)

        with self.subTest("X-Correlation-ID is set on 500 response"):
            correlation_id = str(uuid.uuid4()).upper()
            mock_500()
            response = self.fetch(url, method="GET", headers={'X-Correlation-ID': correlation_id})
            self.assertEqual(response.code, 500)
            self.assertEqual(response.headers.get('X-Correlation-ID'), correlation_id)

        with self.subTest("X-Correlation-ID is set on 400 response"):
            correlation_id = str(uuid.uuid4()).upper()
            response = self.fetch(
                invalid_url, method="GET", headers={'X-Correlation-ID': correlation_id})
            self.assertEqual(response.code, 400)
            self.assertEqual(response.headers.get('X-Correlation-ID'), correlation_id)

    def _test_get_handles_different_accept_header(self, url, expected_json_file_path):
        with self.subTest("Accept header is missing"):
            response = self.fetch(url, method="GET")

            current, expected = self._get_current_and_expected_body(response, expected_json_file_path)

            self.assertEqual(response.code, 200)
            self.assertEqual(expected, current)
            self.assertEqual(response.headers.get(HttpHeaders.CONTENT_TYPE, None), "application/fhir+json")

        with self.subTest("Accept header is case-insensitive application/fhir+json"):
            headers = {'Accept': 'application/fhir+JSON'}
            response = self.fetch(url, method="GET", headers=headers)

            current, expected = self._get_current_and_expected_body(response, expected_json_file_path)

            self.assertEqual(response.code, 200)
            self.assertEqual(expected, current)
            self.assertEqual(response.headers.get(HttpHeaders.CONTENT_TYPE, None), "application/fhir+json")

        with self.subTest("Accept header is invalid"):
            headers = {'Accept': 'invalid-header'}
            response = self.fetch(url, method="GET", headers=headers)

            self.assertEqual(response.code, 406)

    @staticmethod
    def _build_endpoint_url(org_code: Optional[str] = ORG_CODE, service_id: Optional[str] = SERVICE_ID, party_key: Optional[str] = PARTY_KEY):
        url = "/endpoint"

        org_code = f"organization=https://fhir.nhs.uk/Id/ods-organization-code|{org_code}" if org_code else None
        service_id = f"identifier=https://fhir.nhs.uk/Id/nhsEndpointServiceId|{service_id}" if service_id else None
        party_key = f"identifier=https://fhir.nhs.uk/Id/nhsMhsPartyKey|{party_key}" if party_key else None

        query_params = "&".join(filter(lambda query_param: query_param, [org_code, service_id, party_key]))

        url = f"{url}?{query_params}" if query_params else url
        return url

    @staticmethod
    def _build_device_url(
            org_code: Optional[str] = ORG_CODE,
            service_id: Optional[str] = SERVICE_ID,
            party_key: Optional[str] = PARTY_KEY,
            managing_organization: Optional[str] = MANAGING_ORG):

        url = "/device"

        org_code = f"organization=https://fhir.nhs.uk/Id/ods-organization-code|{org_code}" if org_code else None
        service_id = f"identifier=https://fhir.nhs.uk/Id/nhsEndpointServiceId|{service_id}" if service_id else None
        party_key = f"identifier=https://fhir.nhs.uk/Id/nhsMhsPartyKey|{party_key}" if party_key else None
        managing_organization = f"managing-organization=https://fhir.nhs.uk/Id/ods-organization-code|{managing_organization}" if managing_organization else None

        query_params = "&".join(filter(lambda query_param: query_param, [org_code, service_id, party_key, managing_organization]))

        url = f"{url}?{query_params}" if query_params else url
        return url

    @staticmethod
    def _get_current_and_expected_body(response, expected_file_path):
        current = json.loads(message_utilities.replace_uuid(response.body.decode(), FIXED_UUID))
        current_id = current['id']
        current_link_url = current['link'][0]['url']
        current_entry_full_url = current["entry"][0]["fullUrl"]
        current_resource_id = current["entry"][0]["resource"]["id"]

        expected = json.loads(open(expected_file_path, "r").read())
        expected['id'] = current_id
        expected["entry"][0]["fullUrl"] = current_entry_full_url
        expected["entry"][0]["resource"]["id"] = current_resource_id
        expected['link'][0]['url'] = current_link_url

        return current, expected
