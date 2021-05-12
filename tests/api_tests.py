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


def _valid_uri() -> str:
    path = 'Endpoint?organization=https://fhir.nhs.uk/Id/ods-organization-code|L85016&identifier=https://fhir.nhs.uk/Id/nhsServiceInteractionId|urn:nhs:names:services:gpconnect:documents:fhir:rest:search:documentreference-1'
    return path


def _build_test_path(endpoint: str, query_params: dict) -> str:
    def _map_kv(kv: tuple):
        (key, values) = kv
        values = values if isinstance(values, list) else [values]
        return '&'.join(map(lambda value: f'{key}={value}', values))
    
    query_params_string = '&'.join(map(_map_kv, query_params.items()))
    return f'{endpoint}{"?" + query_params_string if query_params_string else ""}'


def _build_endpoint_test_path() -> str:
    return _build_test_path(
        'Endpoint',
        {
            'organization': 'https://fhir.nhs.uk/Id/ods-organization-code|123456',
            'identifier': 'https://fhir.nhs.uk/Id/nhsServiceInteractionId|urn:nhs:names:services:gpconnect:documents:fhir:rest:search:documentreference-1'
        }
    )

ENDPOINT_ORGANIZATION_FHIR_IDENTIFIER = 'https://fhir.nhs.uk/Id/ods-organization-code'
ENDPOINT_INTERACTION_ID_FHIR_IDENTIFIER = 'https://fhir.nhs.uk/Id/nhsServiceInteractionId'
ENDPOINT_PARTY_KEY_FHIR_IDENTIFIER = 'https://fhir.nhs.uk/Id/nhsMhsPartyKey'


@pytest.mark.e2e
@pytest.mark.smoketest
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
            'resource_type': 'Bundle'
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
            'resource_type': 'Bundle'
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
            'resource_type': 'OperationOutcome'
        },
        # condition 4: Endpoint missing mandatory query parameters
        {
            'endpoint': 'Endpoint',
            'query_params': {
                'identifier': f'{ENDPOINT_PARTY_KEY_FHIR_IDENTIFIER}|L85016-822104',
            },
            'status_code': 400,
            'resource_type': 'OperationOutcome'
        },
    ],
    ids=[
        'Endpoint mandatory query parameters present', 
        'Endpoint optional query parameters present',
        'Endpoint unsupported query parameters present',
        'Endpoint missing mandatory query parameters'
    ]
)
# def test_test(request_data: dict):
#     print(_build_test_path(request_data['endpoint'], request_data['query_params']))
async def test_e2e(test_app, api_client: APISessionClient, request_data):
    correlation_id = str(uuid4())
    headers = {
        'apikey': test_app.client_id,
        'x-correlation-id': correlation_id
    }

    uri = _build_test_path(request_data['endpoint'], request_data['query_params'])

    print('path tested: ' + uri)

    async with api_client.get(
        uri,
        headers=headers,
        allow_retries=True
    ) as resp:
        assert resp.status == request_data['status_code']
        body = await resp.json()
        assert 'x-correlation-id' in resp.headers, resp.headers
        assert resp.headers['x-correlation-id'] == correlation_id
        assert body['resourceType'] == request_data['resource_type'], body
        if body['resourceType'] == 'Bundle':
            assert len(body['entry']) == 0, body
            assert body['total'] == 0, body