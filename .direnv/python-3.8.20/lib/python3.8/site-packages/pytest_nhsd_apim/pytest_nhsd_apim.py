"""
This module defines the high-level interface to pytest-nhsd-apim.

These are the fixtures that should be used by your typical proxy.
Testers are expected to want a low-friction method of successfully
completing the auth journey so they can check their desired access
patterns.

Test applications register with the actual products they define.

e.g.:

    - /pathA is only allowed with a user-restricted access token.

    - /pathB allows both user-restricted and some flavour of
      application-restricted.
"""
import pytest

# Note: At runtime, pytest does not follow the imports we define in
# our files. Instead, it just looks amongst all the things it found
# when it imported our extension.  This means we have to import *all*
# of our fixtures into this module even if they are only called as
# dependencies of our public fixtures.
from .apigee_edge import (
    _apigee_app_base_url,
    _apigee_app_base_url_no_dev,
    _apigee_edge_session,
    _apigee_proxy,
    _create_function_scoped_test_app,
    _create_test_app,
    _identity_service_proxy,
    _identity_service_proxy_name,
    _identity_service_proxy_names,
    _proxy_product_with_scope,
    _proxy_products,
    _scope,
    _test_app_callback_url,
    _test_app_credentials,
    _test_app_id,
    apigee_environment,
    identity_service_base_url,
    nhsd_apim_pre_create_app,
    nhsd_apim_proxy_url,
    nhsd_apim_test_app,
    nhsd_apim_unsubscribe_test_app_from_all_products,
    test_app,
    trace,
    products_api,
    access_token_api,
    developer_apps_api
)
from .auth_journey import (
    _jwt_keys,
    get_access_token_via_signed_jwt_flow,
    get_access_token_via_user_restricted_flow_combined_auth,
    get_access_token_via_user_restricted_flow_separate_auth,
    jwt_private_key_pem,
    jwt_public_key,
    jwt_public_key_id,
    jwt_public_key_pem,
    jwt_public_key_url,
)

# Import HOOKS so pytest runs them + config fixtures
from .config import nhsd_apim_api_name, nhsd_apim_config, nhsd_apim_proxy_name, pytest_addoption, pytest_configure
from .log import log, log_method
from .nhsd_apim_authorization import nhsd_apim_authorization
from .secrets import (
    _keycloak_client_credentials,
    _mock_jwks_api_key,
    _status_endpoint_api_key,
    status_endpoint_auth_headers,
)


@pytest.fixture()
def _nhsd_apim_auth_token_data(
    nhsd_apim_authorization,
    _test_app_credentials,
    _test_app_callback_url,
    _keycloak_client_credentials,
    identity_service_base_url,
    jwt_private_key_pem,
    jwt_public_key_id,
    apigee_environment,
):
    """
    Main entrypoint to pytest_nhsd_apim.

    This fixture will examine the @pytest.mark.nhsd_apim_authorization
    on your test and do the rest.
    """

    if nhsd_apim_authorization is None:
        return {}

    access = nhsd_apim_authorization["access"]
    level = nhsd_apim_authorization["level"]
    if access == "application":
        if level == "level0":
            return {"apikey": _test_app_credentials["consumerKey"]}
        elif level == "level3":
            token_data = get_access_token_via_signed_jwt_flow(
                identity_service_base_url,
                _test_app_credentials["consumerKey"],
                jwt_private_key_pem,
                jwt_public_key_id,
                apigee_environment,
                force_new_token=nhsd_apim_authorization["force_new_token"],
            )
            return token_data
        else:
            # Should have been pre-validated.
            raise ValueError(f"Invalid level '{level}' for access 'application'.")

    # User restricted auth flows...
    authentication = nhsd_apim_authorization.get("authentication")
    login_form = nhsd_apim_authorization.get("login_form")

    backend_provider_names = {"healthcare_worker": "nhs-cis2", "patient": "nhs-login"}

    if authentication == "combined":
        token_data = get_access_token_via_user_restricted_flow_combined_auth(
            identity_service_base_url,
            _test_app_credentials["consumerKey"],
            _test_app_credentials["consumerSecret"],
            _test_app_callback_url,
            backend_provider_names[access],
            login_form,
            apigee_environment,
            force_new_token=nhsd_apim_authorization["force_new_token"],
        )

    elif authentication == "separate":
        token_data = get_access_token_via_user_restricted_flow_separate_auth(
            identity_service_base_url,
            _keycloak_client_credentials,
            login_form,
            _test_app_credentials["consumerKey"],
            jwt_private_key_pem,
            jwt_public_key_id,
            backend_provider_names[access],
            apigee_environment,
            force_new_token=nhsd_apim_authorization["force_new_token"],
        )
    else:
        raise ValueError(f"Invalid authentication: {authentication}")
    return token_data


@pytest.fixture()
def nhsd_apim_auth_headers(_nhsd_apim_auth_token_data):
    if "access_token" in _nhsd_apim_auth_token_data:
        return {"Authorization": f"Bearer {_nhsd_apim_auth_token_data['access_token']}"}
    elif "apikey" in _nhsd_apim_auth_token_data:
        return _nhsd_apim_auth_token_data
    return {}
