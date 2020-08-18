import os
import unittest

import requests
from requests import Response


class SdsHttpRequestBuilder(object):
    def __init__(self):
        self.headers = {}
        self.query_params = {}
        self.sds_host = os.environ.get('SDS_ADDRESS', 'http://localhost:9000/endpoint')
        self.assertions = unittest.TestCase('__init__')

    def with_org_code(self, org_code: str):
        self.query_params['org-code'] = org_code
        return self

    def with_service_id(self, service_id: str):
        self.query_params['service-id'] = service_id
        return self

    def with_correlation_id(self, correlation_id: str):
        self.headers["Correlation-Id"] = correlation_id
        return self

    def execute_get_expecting_success(self) -> Response:
        response = self._execute_request()
        self.assertions.assertTrue(
            response.ok,
            f'A non successful error code was returned from server: {response.status_code} {response.text}')

        return response

    def execute_get_expecting_error_response(self) -> Response:
        response = self._execute_request()
        self.assertions.assertTrue(
            response.status_code == 500,
            f'A non 500 error code was returned from server: {response.status_code} {response.text}')

        return response

    def execute_get_expecting_bad_request_response(self) -> Response:
        response = self._execute_request()
        self.assertions.assertTrue(
            response.status_code == 400,
            f'A non 400 error code was returned from server: {response.status_code} {response.text}')

        return response

    def _execute_request(self) -> Response:
        return requests.get(self.sds_host, params=self.query_params, headers=self.headers, verify=False, timeout=15)
