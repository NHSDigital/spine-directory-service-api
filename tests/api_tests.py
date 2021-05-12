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

ENV_VARS = [
    'RELEASE_RELEASEID',
    'SOURCE_COMMIT_ID',
    'APIGEE_ENVIRONMENT',
    'SERVICE_BASE_PATH',
    'STATUS_ENDPOINT_API_KEY',
    'APIGEE_PRODUCT',
    'OAUTH_PROXY',
    'OAUTH_BASE_URI',
    'JWT_PRIVATE_KEY_ABSOLUTE_PATH',
    'ID_TOKEN_NHS_LOGIN_PRIVATE_KEY_ABSOLUTE_PATH',
    'APIGEE_API_TOKEN',
]


# def _base_valid_uri(nhs_number) -> str:
#     return f"FHIR/R4/Immunization?patient.identifier=https://fhir.nhs.uk/Id/nhs-number|{nhs_number}"


# def _valid_uri(nhs_number, procedure_code) -> str:
#     return _base_valid_uri(nhs_number) + f"&procedure-code:below={procedure_code}"


def _valid_uri() -> str:
    return f"FHIR/R4/Endpoint?organization=https://fhir.nhs.uk/Id/ods-organization-code|L85016&identifier=https://fhir.nhs.uk/Id/nhsServiceInteractionId|urn:nhs:names:services:gpconnect:documents:fhir:rest:search:documentreference-1"


@pytest.mark.smoketest
@pytest.mark.asyncio
async def test_test():
    for env_var in ENV_VARS:
        if env_var in os.environ:
            print('{key}: {value}'.format(key=env_var, value=os.environ[env_var]))
        else:
            print('{key} env var not set'.format(key=env_var))


@pytest.mark.smoketest
@pytest.mark.asyncio
async def test_e2e(test_app, api_client: APISessionClient):
    # correlation_id = str(uuid4())
    # authorised_headers["X-Correlation-ID"] = correlation_id
    print("client_id = " + str(test_app.client_id))
    print("test_app = " + str(test_app))
    print("api_client = " + str(api_client))
    authorised_headers = {
        'apikey': test_app.client_id
    }

    async with api_client.get(
        _valid_uri(),
        headers=authorised_headers,
        allow_retries=True
    ) as resp:
        assert resp.status == 200
        body = await resp.json()
        # assert "x-correlation-id" in resp.headers, resp.headers
        # assert resp.headers["x-correlation-id"] == correlation_id
        assert body["resourceType"] == "Bundle", body
        # no data for this nhs number ...
        # assert len(body["entry"]) == 0, body