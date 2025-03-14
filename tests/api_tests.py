
from uuid import uuid4

import pytest
import requests
from uuid import uuid4
from os import getenv


ENDPOINT_ORGANIZATION_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/ods-organization-code"
ENDPOINT_INTERACTION_ID_FHIR_IDENTIFIER = (
    "https://fhir.nhs.uk/Id/nhsServiceInteractionId"
)
ENDPOINT_PARTY_KEY_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/nhsMhsPartyKey"

DEVICE_ORGANIZATION_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/ods-organization-code|YES"
DEVICE_INTERACTION_ID_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/nhsServiceInteractionId"
DEVICE_PARTY_KEY_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/nhsMhsPartyKey"
DEVICE_MANUFACTURING_ORGANIZATION_FHIR_IDENTIFIER = (
    "https://fhir.nhs.uk/Id/ods-organization-code"
)
USE_CPM_ARGUMENT = "iwanttogetdatafromcpm"

IS_PROD = getenv("ENVIRONMENT") in ["int", "prod", "dev", "sandbox"]
IS_DEV = getenv("ENVIRONMENT") in ["dev"]


def _build_test_path(endpoint: str, query_params: dict = None) -> str:
    def _map_kv(kv: tuple):
        (key, values) = kv
        values = values if isinstance(values, list) else [values]
        return "&".join(map(lambda value: f"{key}={value}", values))

    query_params_string = (
        "&".join(map(_map_kv, query_params.items())) if query_params else None
    )
    return f'{endpoint}{"?" + query_params_string if query_params_string else ""}'


@pytest.mark.smoketest
def test_ping(nhsd_apim_proxy_url):
    resp = requests.get(f"{nhsd_apim_proxy_url}/_ping")
    assert resp.status_code == 200


@pytest.mark.smoketest
def test_wait_for_ping(nhsd_apim_proxy_url):
    retries = 0
    resp = requests.get(f"{nhsd_apim_proxy_url}/_ping")
    deployed_commitId = resp.json().get("commitId")

    while (
        deployed_commitId != getenv("SOURCE_COMMIT_ID")
        and retries <= 30
        and resp.status_code == 200
    ):
        resp = requests.get(f"{nhsd_apim_proxy_url}/_ping")
        deployed_commitId = resp.json().get("commitId")
        retries += 1

    if resp.status_code != 200:
        pytest.fail(f"Status code {resp.status_code}, expecting 200")
    elif retries >= 30:
        pytest.fail("Timeout Error - max retries")

    assert deployed_commitId == getenv("SOURCE_COMMIT_ID")


@pytest.mark.smoketest
def test_wait_for_status(nhsd_apim_proxy_url, status_endpoint_auth_headers):
    retries = 0
    resp = requests.get(
        f"{nhsd_apim_proxy_url}/_status", headers=status_endpoint_auth_headers
    )
    deployed_commitId = resp.json().get("commitId")

    while (
        deployed_commitId != getenv("SOURCE_COMMIT_ID")
        and retries <= 30
        and resp.status_code == 200
        and resp.json().get("version")
    ):
        resp = requests.get(
            f"{nhsd_apim_proxy_url}/_status", headers=status_endpoint_auth_headers
        )
        deployed_commitId = resp.json().get("commitId")
        retries += 1

    if resp.status_code != 200:
        pytest.fail(f"Status code {resp.status_code}, expecting 200")
    elif retries >= 30:
        pytest.fail("Timeout Error - max retries")
    elif not resp.json().get("version"):
        pytest.fail("version not found")

    assert deployed_commitId == getenv("SOURCE_COMMIT_ID")


@pytest.mark.securitytest
@pytest.mark.parametrize("endpoint", ["_status", "Endpoint", "Device"])
def test_endpoints_are_secured(nhsd_apim_proxy_url, endpoint):
    resp = requests.get(f"{nhsd_apim_proxy_url}/{endpoint}")
    assert resp.status_code == 401
    body = resp.json()
    assert body["resourceType"] == "OperationOutcome"


@pytest.mark.e2e
@pytest.mark.nhsd_apim_authorization({"access": "application", "level": "level0"})
def test_healthcheck(nhsd_apim_proxy_url, nhsd_apim_auth_headers):
    correlation_id = str(uuid4())
    nhsd_apim_auth_headers["x-correlation-id"] = correlation_id
    nhsd_apim_auth_headers["cache-control"] = "no-cache"

    resp = requests.get(f"{nhsd_apim_proxy_url}/healthcheck/deep", headers=nhsd_apim_auth_headers)
    body = resp.json()

    assert resp.status_code == 200, (
        str(resp.status_code) + " " + str(resp.headers) + " " + str(body)
    )
    assert "x-correlation-id" in resp.headers, resp.headers
    assert resp.headers["x-correlation-id"] == correlation_id
    assert body["status"] == "pass"
    assert body["details"]["ldap"]["status"] == "pass"


@pytest.mark.e2e
@pytest.mark.parametrize(
    "request_data",
    [
        # condition 1: Endpoint organization query parameters present with service id
        {
            "endpoint": "Endpoint",
            "query_params": {
                "organization": f"{ENDPOINT_ORGANIZATION_FHIR_IDENTIFIER}|123456",
                "identifier": f"{ENDPOINT_INTERACTION_ID_FHIR_IDENTIFIER}|urn:nhs:names:services:gpconnect:documents:fhir:rest:search:documentreference-1",
            },
            "status_code": 200,
            "result_count": 0,
        },
        # condition 2: Endpoint organization query parameters present with party key
        {
            "endpoint": "Endpoint",
            "query_params": {
                "organization": f"{ENDPOINT_ORGANIZATION_FHIR_IDENTIFIER}|123456",
                "identifier": f"{ENDPOINT_PARTY_KEY_FHIR_IDENTIFIER}|TEST-PARTY-KEY",
            },
            "status_code": 200,
            "result_count": 0,
        },
        # condition 3: Endpoint all query parameters present
        {
            "endpoint": "Endpoint",
            "query_params": {
                "organization": f"{ENDPOINT_ORGANIZATION_FHIR_IDENTIFIER}|123456",
                "identifier": [
                    f"{ENDPOINT_INTERACTION_ID_FHIR_IDENTIFIER}|urn:nhs:names:services:gpconnect:documents:fhir:rest:search:documentreference-1",
                    f"{ENDPOINT_PARTY_KEY_FHIR_IDENTIFIER}|TEST-PARTY-KEY",
                ],
            },
            "status_code": 200,
            "result_count": 0,
        },
        # condition 4: Endpoint organization query parameter missing but service id and party key present
        {
            "endpoint": "Endpoint",
            "query_params": {
                "identifier": [
                    f"{ENDPOINT_INTERACTION_ID_FHIR_IDENTIFIER}|urn:nhs:names:services:gpconnect:documents:fhir:rest:search:documentreference-1",
                    f"{ENDPOINT_PARTY_KEY_FHIR_IDENTIFIER}|TEST-PARTY-KEY",
                ]
            },
            "status_code": 200,
            "result_count": 0,
        },
        # condition 5: Endpoint unsupported query parameters present
        {
            "endpoint": "Endpoint",
            "query_params": {
                "organization": f"{ENDPOINT_ORGANIZATION_FHIR_IDENTIFIER}|123456",
                "identifier": [
                    f"{ENDPOINT_INTERACTION_ID_FHIR_IDENTIFIER}|urn:nhs:names:services:gpconnect:documents:fhir:rest:search:documentreference-1",
                    f"{ENDPOINT_PARTY_KEY_FHIR_IDENTIFIER}|TEST-PARTY-KEY",
                ],
                "unsupported": "unsupported_parameter_value",
            },
            "status_code": 400,
            "result_count": 0,
        },
        # condition 6: Endpoint missing mandatory query parameters
        {
            "endpoint": "Endpoint",
            "query_params": {
                "identifier": f"{ENDPOINT_PARTY_KEY_FHIR_IDENTIFIER}|TEST-PARTY-KEY",
            },
            "status_code": 400,
            "result_count": 0,
        },
        # condition 7: Endpoint invalid fhir identifier on mandatory query parameter
        {
            "endpoint": "Endpoint",
            "query_params": {
                "organization": "test|123456",
                "identifier": f"{ENDPOINT_INTERACTION_ID_FHIR_IDENTIFIER}|urn:nhs:names:services:gpconnect:documents:fhir:rest:search:documentreference-1",
            },
            "status_code": 400,
            "result_count": 0,
        },
        # condition 8: Device mandatory query parameters present
        {
            "endpoint": "Device",
            "query_params": {
                "organization": f"{DEVICE_ORGANIZATION_FHIR_IDENTIFIER}|123456",
                "identifier": f"{DEVICE_INTERACTION_ID_FHIR_IDENTIFIER}|urn:nhs:names:services:psis:REPC_IN150016UK05",
            },
            "status_code": 200,
            "result_count": 0,
        },
        # condition 9: Device optional query parameters present
        {
            "endpoint": "Device",
            "query_params": {
                "organization": f"{DEVICE_ORGANIZATION_FHIR_IDENTIFIER}|123456",
                "identifier": [
                    f"{DEVICE_INTERACTION_ID_FHIR_IDENTIFIER}|urn:nhs:names:services:psis:REPC_IN150016UK05",
                    f"{DEVICE_PARTY_KEY_FHIR_IDENTIFIER}|TEST-PARTY-KEY",
                ],
                "manufacturing-organization": f"{DEVICE_MANUFACTURING_ORGANIZATION_FHIR_IDENTIFIER}|YES",
            },
            "status_code": 200,
            "result_count": 0,
        },
        # condition 10: Device unsupported query parameters present
        {
            "endpoint": "Device",
            "query_params": {
                "organization": f"{DEVICE_ORGANIZATION_FHIR_IDENTIFIER}|123456",
                "identifier": [
                    f"{DEVICE_INTERACTION_ID_FHIR_IDENTIFIER}|urn:nhs:names:services:psis:REPC_IN150016UK05",
                    f"{DEVICE_PARTY_KEY_FHIR_IDENTIFIER}|TEST-PARTY-KEY",
                ],
                "manufacturing-organization": f"{DEVICE_MANUFACTURING_ORGANIZATION_FHIR_IDENTIFIER}|YES",
                "unsupported": "unsupported_parameter_value",
            },
            "status_code": 400,
            "result_count": 0,
        },
        # condition 11: Device missing mandatory query parameters
        {
            "endpoint": "Device",
            "query_params": {
                "identifier": [
                    f"{DEVICE_INTERACTION_ID_FHIR_IDENTIFIER}|urn:nhs:names:services:psis:REPC_IN150016UK05",
                    f"{DEVICE_PARTY_KEY_FHIR_IDENTIFIER}|TEST-PARTY-KEY",
                ],
                "manufacturing-organization": f"{DEVICE_MANUFACTURING_ORGANIZATION_FHIR_IDENTIFIER}|YES",
                "unsupported": "unsupported_parameter_value",
            },
            "status_code": 400,
            "result_count": 0,
        },
        # condition 12: Device invalid fhir identifier on mandatory query parameter
        {
            "endpoint": "Device",
            "query_params": {
                "organization": "test|123456",
                "identifier": f"{DEVICE_INTERACTION_ID_FHIR_IDENTIFIER}|urn:nhs:names:services:psis:REPC_IN150016UK05",
            },
            "status_code": 400,
            "result_count": 0,
        },
    ],
    ids=[
        "condition 1: Endpoint organization query parameters present with service id",
        "condition 2: Endpoint optional query parameters present with party key",
        "condition 3: Endpoint all query parameters present",
        "condition 4: Endpoint organization query parameter missing but service id and party key present",
        "condition 5: Endpoint unsupported query parameters present",
        "condition 6: Endpoint missing mandatory query parameters",
        "condition 7: Endpoint invalid fhir identifier on mandatory query parameter",
        "condition 8: Device mandatory query parameters present",
        "condition 9: Device optional query parameters present",
        "condition 10: Device unsupported query parameters present",
        "condition 11: Device missing mandatory query parameters",
        "condition 12: Device invalid fhir identifier on mandatory query parameter",
    ],
)
@pytest.mark.nhsd_apim_authorization({"access": "application", "level": "level0"})
def test_endpoints(nhsd_apim_proxy_url, nhsd_apim_auth_headers, request_data):
    correlation_id = str(uuid4())
    nhsd_apim_auth_headers["x-correlation-id"] = correlation_id
    nhsd_apim_auth_headers["cache-control"] = "no-cache"

    query_params = request_data["query_params"]
    path = _build_test_path(request_data["endpoint"], query_params)
    uri = f"{nhsd_apim_proxy_url}/{path}"
    _assert_response(
        uri,
        nhsd_apim_auth_headers,
        request_data["result_count"],
        request_data["status_code"],
        correlation_id,
    )


def _assert_response(url, headers, result_count, expected_status, correlation_id):
    resp = requests.get(url, headers=headers)
    body = resp.json()
    assert resp.status_code == expected_status, (
        str(resp.status_code) + " " + str(resp.headers) + " " + str(body)
    )
    assert "x-correlation-id" in resp.headers, resp.headers
    assert resp.headers["x-correlation-id"] == correlation_id
    resource_type = body["resourceType"]
    if resp.status_code == 200:
        assert resource_type == "Bundle", body
        assert len(body["entry"]) == result_count, body
        assert body["total"] == result_count, body
    else:
        assert resource_type == "OperationOutcome", body
