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

DEVICE_ORGANIZATION_FHIR_IDENTIFIER = 'https://fhir.nhs.uk/Id/ods-organization-code|YES'
DEVICE_INTERACTION_ID_FHIR_IDENTIFIER = 'https://fhir.nhs.uk/Id/nhsServiceInteractionId'
DEVICE_PARTY_KEY_FHIR_IDENTIFIER = 'https://fhir.nhs.uk/Id/nhsMhsPartyKey'
DEVICE_MANAGING_ORGANIZATION_FHIR_IDENTIFIER = 'https://fhir.nhs.uk/Id/ods-organization-code'


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
                'organization': f'{DEVICE_INTERACTION_ID_FHIR_IDENTIFIER}|123456',
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
                'organization': f'{DEVICE_INTERACTION_ID_FHIR_IDENTIFIER}|123456',
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
    ]
)
# def test_test(request_data: dict):
#     print(_build_test_path(request_data['endpoint'], request_data['query_params']))
async def test_e2e(test_app, api_client: APISessionClient, request_data):
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
        assert resp.status == request_data['status_code']
        body = await resp.json()
        assert 'x-correlation-id' in resp.headers, resp.headers
        assert resp.headers['x-correlation-id'] == correlation_id
        resource_type = body['resourceType']
        if resp.status == 200:
            assert resource_type == 'Bundle'
            assert len(body['entry']) == 0, body
            assert body['total'] == 0, body
        else:
            assert resource_type == 'OperationOutcome'
