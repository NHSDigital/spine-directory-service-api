from typing import List
from uuid import uuid4
from time import time, sleep
from tests import conftest
import pytest
import os
from aiohttp import ClientResponse
from api_test_utils import env
from api_test_utils import poll_until
from api_test_utils.api_session_client import APISessionClient
from api_test_utils.api_test_session_config import APITestSessionConfig


ENDPOINT_ORGANIZATION_FHIR_IDENTIFIER = 'https://fhir.nhs.uk/Id/ods-organization-code'
ENDPOINT_INTERACTION_ID_FHIR_IDENTIFIER = 'https://fhir.nhs.uk/Id/nhsServiceInteractionId'
ENDPOINT_PARTY_KEY_FHIR_IDENTIFIER = 'https://fhir.nhs.uk/Id/nhsMhsPartyKey'

DEVICE_ORGANIZATION_FHIR_IDENTIFIER = 'https://fhir.nhs.uk/Id/ods-organization-code|YES'
DEVICE_INTERACTION_ID_FHIR_IDENTIFIER = 'https://fhir.nhs.uk/Id/nhsServiceInteractionId'
DEVICE_PARTY_KEY_FHIR_IDENTIFIER = 'https://fhir.nhs.uk/Id/nhsMhsPartyKey'
DEVICE_MANAGING_ORGANIZATION_FHIR_IDENTIFIER = 'https://fhir.nhs.uk/Id/ods-organization-code'


def _build_test_path(endpoint: str, query_params: dict = None) -> str:
    def _map_kv(kv: tuple):
        (key, values) = kv
        values = values if isinstance(values, list) else [values]
        return '&'.join(map(lambda value: f'{key}={value}', values))
    
    query_params_string = '&'.join(map(_map_kv, query_params.items())) if query_params else None
    return f'{endpoint}{"?" + query_params_string if query_params_string else ""}'


def _dict_path(raw, path: List[str]):
    if not raw:
        return raw

    if not path:
        return raw

    res = raw.get(path[0])
    if not res or len(path) == 1 or type(res) != dict:
        return res

    return _dict_path(res, path[1:])


@pytest.mark.e2e
@pytest.mark.smoketest
def test_output_test_config(api_test_config: APITestSessionConfig):
    print(api_test_config)


@pytest.mark.e2e
@pytest.mark.smoketest
@pytest.mark.asyncio
async def test_wait_for_ping(api_client: APISessionClient, api_test_config: APITestSessionConfig):
    async def apigee_deployed(resp: ClientResponse):
        if resp.status != 200:
            return False

        body = await resp.json()
        return body.get("commitId") == api_test_config.commit_id

    await poll_until(
        make_request=lambda: api_client.get("_ping"), until=apigee_deployed, timeout=30
    )


@pytest.mark.e2e
@pytest.mark.smoketest
@pytest.mark.asyncio
async def test_check_status_is_secured(api_client: APISessionClient):
    async with api_client.get("_status", allow_retries=True) as resp:
        assert resp.status == 401
        body = await resp.json()
        assert body['resourceType'] == 'OperationOutcome'


@pytest.mark.e2e
@pytest.mark.smoketest
@pytest.mark.asyncio
async def test_wait_for_status(api_client: APISessionClient, api_test_config: APITestSessionConfig):
    async def is_deployed(resp: ClientResponse):
        if resp.status != 200:
            return False

        body = await resp.json()

        if body.get("commitId") != api_test_config.commit_id:
            return False

        backend = _dict_path(body, ["checks", "healthcheck", "outcome", "version"])
        if not backend:
            return True

        return backend.get("commitId") == api_test_config.commit_id

    deploy_timeout = 120 if api_test_config.api_environment.endswith("sandbox") else 30

    await poll_until(
        make_request=lambda: api_client.get(
            "_status", headers={"apikey": env.status_endpoint_api_key()}
        ),
        until=is_deployed,
        timeout=deploy_timeout,
    )


@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint", ["Endpoint", "Device"])
async def test_endpoints_are_secured(api_client: APISessionClient, endpoint):
    async with api_client.get(_build_test_path(endpoint), allow_retries=True) as resp:
        assert resp.status == 401
        body = await resp.json()
        assert body['resourceType'] == 'OperationOutcome'


@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "request_data",
    [
        # condition 1: Endpoint mandatory query parameters present
        {
            'endpoint': 'Endpoint',
            'query_params': {
                'organization': f'{ENDPOINT_ORGANIZATION_FHIR_IDENTIFIER}|123456',
                'identifier': f'{ENDPOINT_INTERACTION_ID_FHIR_IDENTIFIER}|urn:nhs:names:services:gpconnect:documents:fhir:rest:search:documentreference-1',
            },
            'status_code': 200,
        },
        # condition 2: Endpoint optional query parameters present
        {
            'endpoint': 'Endpoint',
            'query_params': {
                'organization': f'{ENDPOINT_ORGANIZATION_FHIR_IDENTIFIER}|123456',
                'identifier': [
                    f'{ENDPOINT_INTERACTION_ID_FHIR_IDENTIFIER}|urn:nhs:names:services:gpconnect:documents:fhir:rest:search:documentreference-1',
                    f'{ENDPOINT_PARTY_KEY_FHIR_IDENTIFIER}|L85016-822104',
                ]
            },
            'status_code': 200,
        },
        # condition 3: Endpoint unsupported query parameters present
        {
            'endpoint': 'Endpoint',
            'query_params': {
                'organization': f'{ENDPOINT_ORGANIZATION_FHIR_IDENTIFIER}|123456',
                'identifier': [
                    f'{ENDPOINT_INTERACTION_ID_FHIR_IDENTIFIER}|urn:nhs:names:services:gpconnect:documents:fhir:rest:search:documentreference-1',
                    f'{ENDPOINT_PARTY_KEY_FHIR_IDENTIFIER}|L85016-822104',
                ],
                'unsupported': 'unsupported_parameter_value',
            },
            'status_code': 400,
        },
        # condition 4: Endpoint missing mandatory query parameters
        {
            'endpoint': 'Endpoint',
            'query_params': {
                'identifier': f'{ENDPOINT_PARTY_KEY_FHIR_IDENTIFIER}|L85016-822104',
            },
            'status_code': 400,
        },
        # condition 5: Endpoint invalid fhir identifier on mandatory query parameter
        {
            'endpoint': 'Endpoint',
            'query_params': {
                'organization': 'test|123456',
                'identifier': f'{ENDPOINT_INTERACTION_ID_FHIR_IDENTIFIER}|urn:nhs:names:services:gpconnect:documents:fhir:rest:search:documentreference-1',
            },
            'status_code': 400,
        },
        # condition 6: Device mandatory query parameters present
        {
            'endpoint': 'Device',
            'query_params': {
                'organization': f'{DEVICE_ORGANIZATION_FHIR_IDENTIFIER}|123456',
                'identifier': f'{DEVICE_INTERACTION_ID_FHIR_IDENTIFIER}|urn:nhs:names:services:psis:REPC_IN150016UK05',
            },
            'status_code': 200,
        },
        # condition 7: Device optional query parameters present
        {
            'endpoint': 'Device',
            'query_params': {
                'organization': f'{DEVICE_ORGANIZATION_FHIR_IDENTIFIER}|123456',
                'identifier': [
                    f'{DEVICE_INTERACTION_ID_FHIR_IDENTIFIER}|urn:nhs:names:services:psis:REPC_IN150016UK05',
                    f'{DEVICE_PARTY_KEY_FHIR_IDENTIFIER}|L85016-822104',
                ],
                'managing-organization': f'{DEVICE_MANAGING_ORGANIZATION_FHIR_IDENTIFIER}|YES',
            },
            'status_code': 200,
        },
        # condition 8: Device unsupported query parameters present
        {
            'endpoint': 'Device',
            'query_params': {
                'organization': f'{DEVICE_ORGANIZATION_FHIR_IDENTIFIER}|123456',
                'identifier': [
                    f'{DEVICE_INTERACTION_ID_FHIR_IDENTIFIER}|urn:nhs:names:services:psis:REPC_IN150016UK05',
                    f'{DEVICE_PARTY_KEY_FHIR_IDENTIFIER}|L85016-822104',
                ],
                'managing-organization': f'{DEVICE_MANAGING_ORGANIZATION_FHIR_IDENTIFIER}|YES',
                'unsupported': 'unsupported_parameter_value',
            },
            'status_code': 400,
        },
        # condition 9: Device missing mandatory query parameters
        {
            'endpoint': 'Device',
            'query_params': {
                'identifier': [
                    f'{DEVICE_INTERACTION_ID_FHIR_IDENTIFIER}|urn:nhs:names:services:psis:REPC_IN150016UK05',
                    f'{DEVICE_PARTY_KEY_FHIR_IDENTIFIER}|L85016-822104',
                ],
                'managing-organization': f'{DEVICE_MANAGING_ORGANIZATION_FHIR_IDENTIFIER}|YES',
                'unsupported': 'unsupported_parameter_value',
            },
            'status_code': 400,
        },
        # condition 10: Device invalid fhir identifier on mandatory query parameter
        {
            'endpoint': 'Device',
            'query_params': {
                'organization': 'test|123456',
                'identifier': f'{DEVICE_INTERACTION_ID_FHIR_IDENTIFIER}|urn:nhs:names:services:psis:REPC_IN150016UK05',
            },
            'status_code': 400,
        },
    ],
    ids=[
        'condition 1: Endpoint mandatory query parameters present',
        'condition 2: Endpoint optional query parameters present',
        'condition 3: Endpoint unsupported query parameters present',
        'condition 4: Endpoint missing mandatory query parameters',
        'condition 5: Endpoint invalid fhir identifier on mandatory query parameter',
        'condition 6: Device mandatory query parameters present',
        'condition 7: Device optional query parameters present',
        'condition 8: Device unsupported query parameters present',
        'condition 9: Device missing mandatory query parameters',
        'condition 10: Device invalid fhir identifier on mandatory query parameter',
    ]
)
async def test_endpoints(test_app, api_client: APISessionClient, request_data):
    correlation_id = str(uuid4())
    headers = {
        'apikey': test_app.client_id,
        'x-correlation-id': correlation_id,
        'cache-control': 'no-cache',
    }

    uri = _build_test_path(request_data['endpoint'], request_data['query_params'])

    async with api_client.get(
        uri,
        headers=headers,
        allow_retries=True
    ) as resp:
        body = await resp.json()
        assert resp.status == request_data['status_code'], str(resp.status) + " " + str(body)
        assert 'x-correlation-id' in resp.headers, resp.headers
        assert resp.headers['x-correlation-id'] == correlation_id
        resource_type = body['resourceType']
        if resp.status == 200:
            assert resource_type == 'Bundle', body
            assert len(body['entry']) == 0, body
            assert body['total'] == 0, body
        else:
            assert resource_type == 'OperationOutcome', body
