import os

@pytest.mark.e2e
@pytest.mark.smoketest
async def test_test():
    print(os.environ['APIGEE_ENVIRONMENT'])
    print(os.environ['SERVICE_BASE_PATH'])
    print(os.environ['APIGEE_PRODUCT'])
    print(os.environ['APIGEE_API_TOKEN'])