# flake8: noqa
import asyncio
from time import time
from uuid import uuid4
import os
import pytest
from api_test_utils.api_test_session_config import APITestSessionConfig
from api_test_utils.fixtures import api_client  # pylint: disable=unused-import
from api_test_utils.apigee_api_apps import ApigeeApiDeveloperApps
from api_test_utils.apigee_api_products import ApigeeApiProducts
from api_test_utils.oauth_helper import OauthHelper


@pytest.fixture(scope="session")
def test_app():
    """Setup & Teardown an app-restricted app for this api"""
    app = ApigeeApiDeveloperApps()
    loop = asyncio.new_event_loop()
    loop.run_until_complete(
        app.setup_app(
            api_products=[get_env("APIGEE_PRODUCT")],
            # custom_attributes={
                # "jwks-resource-url": "https://raw.githubusercontent.com/NHSDigital/identity-service-jwks/main/jwks/internal-dev/9baed6f4-1361-4a8e-8531-1f8426e3aba8.json"  # noqa
            # },
        )
    )
    # app.oauth = OauthHelper(app.client_id, app.client_secret, app.callback_url)
    yield app
    loop.run_until_complete(app.destroy_app())

