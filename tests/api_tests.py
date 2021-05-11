import os
import pytest

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

@pytest.mark.e2e
@pytest.mark.smoketest
@pytest.mark.asyncio
async def test_test():
    for env_var in ENV_VARS:
        if env_var in os.environ:
            print('{key}: {value}'.format(key=env_var, value=os.environ[env_var]))
        else:
            print('{key} env var not set'.format(key=env_var))
