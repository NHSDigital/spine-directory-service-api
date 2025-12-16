"""
Fixtures which interact with Apigee Edge API.

This includes app setup/teardown, getting proxy info (proxy-under-test
+ identity-service of choice), getting products, registering them with
the test app.
"""
import functools
import warnings
from datetime import datetime
from typing import Callable
from uuid import uuid4

import pytest
import requests

from .log import log, log_method
from .apigee_apis import (
    ApigeeNonProdCredentials,
    ApigeeClient,
    DebugSessionsAPI,
    AccessTokensAPI,
    ApiProductsAPI,
    DeveloperAppsAPI
)

APIGEE_BASE_URL = "https://api.enterprise.apigee.com/v1/"


@pytest.fixture(scope="session")
@log_method
def _apigee_edge_session(nhsd_apim_config):
    """
    A `requests` session with the correct auth header.
    """
    token = nhsd_apim_config["APIGEE_ACCESS_TOKEN"]
    session = requests.session()
    session.headers = {"Authorization": f"Bearer {token}"}
    return session


@pytest.fixture(scope="session")
@log_method
def _apigee_app_base_url(nhsd_apim_config):
    org = nhsd_apim_config["APIGEE_ORGANIZATION"]
    dev = nhsd_apim_config["APIGEE_DEVELOPER"]
    url = APIGEE_BASE_URL + f"organizations/{org}/developers/{dev}/apps"
    return url

@pytest.fixture(scope="session")
@log_method
def _apigee_app_base_url_no_dev(nhsd_apim_config):
    org = nhsd_apim_config["APIGEE_ORGANIZATION"]
    url = APIGEE_BASE_URL + f"organizations/{org}/apps"
    return url

@functools.lru_cache(maxsize=None)
@log_method
def _get_proxy_json(session, nhsd_apim_proxy_url):
    """
    Query the apigee edge API to get data about the desired proxy, in particular its current deployment.
    """
    deployment_err_msg = (
        "\n\tFailed to retrieve the proxy deployment data. " +
        "Please check the validity of the APIGEE credentials and token as well as any headers."
    )
    deployment_resp = session.get(f"{nhsd_apim_proxy_url}/deployments")
    assert deployment_resp.status_code == 200, deployment_err_msg.format(deployment_resp.content)
    deployment_json = deployment_resp.json()

    # Should be the case
    assert len(deployment_json["environment"]) == 1

    deployed_revision = next(
        filter(
            lambda d: d["state"] == "deployed",
            deployment_json["environment"][0]["revision"],
        )
    )
    revision = deployed_revision["name"]
    proxy_resp = session.get(nhsd_apim_proxy_url + f"/revisions/{revision}")
    assert proxy_resp.status_code == 200
    proxy_json = proxy_resp.json()
    proxy_json["environment"] = deployment_json["environment"][0]["name"]
    return proxy_json


@pytest.fixture()
def _identity_service_proxy(_apigee_edge_session, nhsd_apim_config, _identity_service_proxy_name):
    """
    Get the current revision deployed and pull proxy metadata.
    """
    if not _identity_service_proxy_name:
        return
    org = nhsd_apim_config["APIGEE_ORGANIZATION"]
    url = APIGEE_BASE_URL + f"organizations/{org}/apis/{_identity_service_proxy_name}"
    return _get_proxy_json(_apigee_edge_session, url)


@pytest.fixture()
@log_method
def _apigee_proxy(_apigee_edge_session, nhsd_apim_config, nhsd_apim_proxy_name):
    """
    Get the current revision deployed and pull proxy metadata.
    """
    org = nhsd_apim_config["APIGEE_ORGANIZATION"]
    apigee_edge_api_proxy_url = APIGEE_BASE_URL + f"organizations/{org}/apis/{nhsd_apim_proxy_name}"
    return _get_proxy_json(_apigee_edge_session, apigee_edge_api_proxy_url)


@log_method
def get_all_products(_apigee_edge_session, nhsd_apim_config):
    got_all_products = False
    org = nhsd_apim_config["APIGEE_ORGANIZATION"]
    products_url = APIGEE_BASE_URL + f"organizations/{org}/apiproducts"
    params = {"expand": "true"}
    products = []
    while not got_all_products:
        resp = _apigee_edge_session.get(products_url, params=params)
        new_products = resp.json()["apiProduct"]
        products.extend(new_products)
        if len(new_products) == 1000:
            last = products.pop()
            params.update({"startKey": last["name"]})
        else:
            got_all_products = True
    return products


_APIGEE_PRODUCTS = []


@pytest.fixture()
@log_method
def _proxy_products(_apigee_edge_session, nhsd_apim_proxy_name, nhsd_apim_config):
    """
    Find all products that grant access to your proxy (by name).

    In the case of open-access to an API, ensure this is not called as
    it raises an exception when there are no matches.

    This also allows us to skip checking whether the returned list is
    empty in other fixtures.
    """
    global _APIGEE_PRODUCTS
    proxy_products = [product for product in _APIGEE_PRODUCTS if nhsd_apim_proxy_name in product["proxies"]]

    if len(proxy_products) == 0:
        # Refresh the list and try again...
        _APIGEE_PRODUCTS = get_all_products(_apigee_edge_session, nhsd_apim_config)

    proxy_products = [product for product in _APIGEE_PRODUCTS if nhsd_apim_proxy_name in product["proxies"]]
    if len(proxy_products) == 0:
        raise ValueError(f"No products grant access to proxy {nhsd_apim_proxy_name}")

    return proxy_products


@log_method
def _get_proxy_url(proxy_json):
    """
    Construct the proxy url from the proxy_json
    """
    env = proxy_json["environment"]
    prefix = "https://"
    if env != "prod":
        prefix += f"{env}."
    proxy_url = prefix + "api.service.nhs.uk/" + proxy_json["basepaths"][0]
    return proxy_url


@pytest.fixture()
@log_method
def nhsd_apim_proxy_url(_apigee_proxy):
    """
    Base URL of the proxy under test.
    """
    return _get_proxy_url(_apigee_proxy)


@pytest.fixture()
@log_method
def apigee_environment(_apigee_proxy):
    """
    Apigee environment of the proxy under test.
    """
    return _apigee_proxy["environment"]


@pytest.fixture()
@log_method
def identity_service_base_url(_identity_service_proxy):
    """
    Base URL of the identity-service proxy we will use to authenticate.
    """
    if _identity_service_proxy is None:
        return None
    return _get_proxy_url(_identity_service_proxy)


@pytest.fixture()
@log_method
def _scope(nhsd_apim_authorization):
    """
    Get APIGEE proxy `scope`.
    """
    if not isinstance(nhsd_apim_authorization, type(None)):
        return nhsd_apim_authorization.get("scope")

    return


@pytest.fixture()
@log_method
def _identity_service_proxy_names(_proxy_product_with_scope):
    """
    Get a list of `identity-service` proxies for which we can match a given/required APIGEE `scope`.
    """
    return [proxy for proxy in _proxy_product_with_scope["proxies"] if proxy.startswith("identity-service")]


@pytest.fixture()
@log_method
def _identity_service_proxy_name(_identity_service_proxy_names, nhsd_apim_authorization):
    """
    Make a reasonable choice about which identity-service proxy to use.

    We have a keycloak instance, which is a proper OIDC provider, which is
    pointed to by identity-service proxies with "mock" in the name.

    Return None if there's no identity-service proxies, though this should
    probably never happen.
    """
    if not _identity_service_proxy_names:  # empty list
        return None
    if not nhsd_apim_authorization:
        return None

    keycloak = next(filter(lambda name: "-mock" in name, _identity_service_proxy_names), None)
    if keycloak:
        return keycloak
    warnings.warn(f"Unable to find mock auth generation 2 in {_identity_service_proxy_names}.")
    return _identity_service_proxy_names[0]


@pytest.fixture()
@log_method
def _proxy_product_with_scope(_scope, _proxy_products, nhsd_apim_proxy_name):
    """
    The first product with a scope matching the one specified by the
    pytest.marker.product_scope fixture.

    If the required _scope is None then just returns the first
    product. Otherwise, finds a product that has the required scope.

    Raises an exception if there are no matches.

    This allows us to assume (in other fixtures) that this function
    always returns a product.
    """
    if _scope is None:
        # Any product referencing the proxy under test is fine, so
        # return the first one.
        return _proxy_products[0]
    for product in _proxy_products:
        if _scope in product["scopes"]:
            return product
    error_msg = f"No product granting access to proxy under test has scope `{_scope}`"
    log.error(error_msg)
    raise ValueError(error_msg)


@pytest.fixture(scope="session")
@log_method
def test_app(nhsd_apim_test_app) -> Callable:
    warnings.warn(f"test_app fixture is deprecated. Use nhsd_apim_test_app instead.")
    return nhsd_apim_test_app


_TEST_APP = None


@pytest.fixture(scope="session")
@log_method
def nhsd_apim_test_app(_create_test_app, _apigee_edge_session, _apigee_app_base_url, _apigee_app_base_url_no_dev, _test_app_id) -> Callable:
    """
    A Callable that gets you the current state of the test app.
    """

    # pytest fixtures are wonderful, and do lots of magical things.
    #
    # But...
    #
    # In any well developed pytest extension, one ends up with a
    # complicated dependency graph of fixtures calling other fixtures
    # calling fixtures. In some of these fixtures we want the
    # "current-state" of our app. But some in fixtures we want to
    # update the state of the app. Which fixture gets called first?
    # The answer is... it's really hard to know.
    #
    # As much as I love pytest-provided caching, it's safest to let
    # Apigee be the sole arbiter of the current state of our test app
    # at the cost of an API call.  Therefore, I'm returning a callable
    # rather than JSON from this fixture.
    #
    # If we get the higher level abstractions right in this
    # pytest-extension, a run-of-the-mill user won't need to know much
    # about the app at all, they will just have credentials to call
    # their api.
    def app(force_refresh=False):
        global _TEST_APP
        if _TEST_APP and not force_refresh:
            return _TEST_APP
        if _test_app_id:
            resp = _apigee_edge_session.get(_apigee_app_base_url_no_dev + "/" + _test_app_id)
        else: 
            resp = _apigee_edge_session.get(_apigee_app_base_url + "/" + _create_test_app["name"])
        _TEST_APP = resp.json()
        return _TEST_APP

    return app


@log_method
@pytest.fixture(scope="session")
def nhsd_apim_unsubscribe_test_app_from_all_products(
    nhsd_apim_test_app, _apigee_edge_session, _apigee_app_base_url, _test_app_id
):
    """
    Returns a callable that when run, will unsubscribe the test app
    from all products.

    If you have test code which dynamically creates/destroys products,
    you may need to bring in this callable and execute it.
    """

    def unsubscribe():
        # If app already exists we don't want to modify
        # its product subscriptions
        if _test_app_id:
            return

        app = nhsd_apim_test_app(force_refresh=True)
        app_name = app["name"]
        for cred in app["credentials"]:
            key = cred["consumerKey"]
            resp = _apigee_edge_session.delete(_apigee_app_base_url + f"/{app_name}/keys/{key}")
        app = nhsd_apim_test_app(force_refresh=True)

    return unsubscribe


@log_method
def get_matching_creds(app, product_name):
    """
    Takes some app JSON and gets credentials
    """

    def approved(x):
        return x["status"] == "approved"

    now = int(1000 * datetime.utcnow().timestamp())
    for creds in filter(approved, app["credentials"]):
        if creds["expiresAt"] == -1 or now < creds["expiresAt"]:
            approved_product_names = [p["apiproduct"] for p in filter(approved, creds["apiProducts"])]
            if product_name in approved_product_names:
                return creds


@log_method
def get_app_credentials_for_product(apigee_app_base_url, apigee_edge_session, app, product_name, _test_app_id):
    matching_creds = get_matching_creds(app, product_name)
    if matching_creds is not None:
        return matching_creds

    # If app already exists we do not want to modify its
    # subscriptions.
    if not _test_app_id == "":
        raise ValueError(f"App with id {_test_app_id} does not have expected credentials")

    # Use the apigee edge api to add another set of credentials
    # https://apidocs.apigee.com/docs/developer-apps/1/routes/organizations/%7Borg_name%7D/developers/%7Bdeveloper_email%7D/apps/%7Bapp_name%7D/put
    app["apiProducts"] = [product_name]
    app_url = apigee_app_base_url + "/" + app["name"]
    resp = apigee_edge_session.put(app_url, json=app)
    if resp.status_code != 200:
        raise ValueError(f"Unexpected response from {app_url}: {resp.status_code}, {resp.text}")
    global _TEST_APP
    _TEST_APP = resp.json()

    matching_creds = get_matching_creds(_TEST_APP, product_name)
    return matching_creds


@pytest.fixture()
@log_method
def _test_app_credentials(
    _apigee_app_base_url,
    _apigee_edge_session,
    nhsd_apim_test_app,
    _scope,
    _proxy_product_with_scope,
    _test_app_id,
):
    """
    Get matching credentials for `test_app`, which have access
    to the EXACT set of desired products requested by the user.
    """
    app = nhsd_apim_test_app()
    return get_app_credentials_for_product(
        _apigee_app_base_url,
        _apigee_edge_session,
        app,
        _proxy_product_with_scope["name"],
        _test_app_id,
    )


@pytest.fixture(scope="session")
@log_method
def _apigee_edge_session(nhsd_apim_config):
    """
    Create an APIGEE `requests` session.
    """
    token = nhsd_apim_config["APIGEE_ACCESS_TOKEN"]
    session = requests.session()
    session.headers = {"Authorization": f"Bearer {token}"}
    return session


@pytest.fixture(scope="session")
def nhsd_apim_pre_create_app():
    """
    Hook fixture upon which to hang any methods you wish to call prior
    to creating the test app.
    """
    yield


@pytest.fixture(scope="session")
@log_method
def _create_test_app(
    _apigee_app_base_url,
    _apigee_app_base_url_no_dev,
    _apigee_edge_session,
    jwt_public_key_url,
    nhsd_apim_pre_create_app,
    _test_app_id,
):
    """
    Create an ephemeral app that lasts the duration of the pytest
    session.

    Note that a single app can have many sets of credentials.  Each
    set of credentials can be subscribed to a unique set of products,
    so one app can test your API against multiple product
    configurations should you need to do so.  See `app_credentials`
    for details.
    """

    # Retrieving pre-existing app
    if not _test_app_id == "":
        get_resp = _apigee_edge_session.get(_apigee_app_base_url_no_dev + "/" + _test_app_id)
        err_msg = f"Could not GET TestApp: {_test_app_id}.\tReason: {get_resp.text}"
        assert get_resp.status_code == 200, err_msg
        yield get_resp.json()
    else:
        app = {
            "name": f"apim-auto-{uuid4()}",
            "callbackUrl": "https://example.org/callback",
            "attributes": [{"name": "jwks-resource-url", "value": jwt_public_key_url}],
        }
        create_resp = _apigee_edge_session.post(_apigee_app_base_url, json=app)
        err_msg = f"Could not CREATE TestApp: `{app['name']}`.\tReason: {create_resp.text}"
        assert create_resp.status_code == 201, err_msg

        yield create_resp.json()
        delete_resp = _apigee_edge_session.delete(_apigee_app_base_url + "/" + app["name"])
        err_msg = f"Could not DELETE TestApp: `{app['name']}`.\tReason: {delete_resp.text}"
        assert delete_resp.status_code == 200, err_msg
    global _TEST_APP
    _TEST_APP = None


@pytest.fixture(scope="function")
@log_method
def _create_function_scoped_test_app(
    _apigee_app_base_url,
    _apigee_edge_session,
    jwt_public_key_url,
    nhsd_apim_pre_create_app,
    _test_app_id,
):
    """
    Create an ephemeral app that lasts the duration of the pytest
    test.

    Note that a single app can have many sets of credentials.  Each
    set of credentials can be subscribed to a unique set of products,
    so one app can test your API against multiple product
    configurations should you need to do so.  See `app_credentials`
    for details.
    """

    # Retrieving pre-existing app
    if not _test_app_id == "":
        get_resp = _apigee_edge_session.get(_apigee_app_base_url_no_dev + "/" + _test_app_id)
        err_msg = f"Could not GET TestApp: {_test_app_id}.\tReason: {get_resp.text}"
        assert get_resp.status_code == 200, err_msg
        yield get_resp.json()
    else:
        app = {
            "name": f"apim-auto-{uuid4()}",
            "callbackUrl": "https://example.org/callback",
            "attributes": [{"name": "jwks-resource-url", "value": jwt_public_key_url}],
        }
        create_resp = _apigee_edge_session.post(_apigee_app_base_url, json=app)
        err_msg = f"Could not CREATE TestApp: `{app['name']}`.\tReason: {create_resp.text}"
        assert create_resp.status_code == 201, err_msg

        yield create_resp.json()
        delete_resp = _apigee_edge_session.delete(_apigee_app_base_url + "/" + app["name"])
        err_msg = f"Could not DELETE TestApp: `{app['name']}`.\tReason: {delete_resp.text}"
        assert delete_resp.status_code == 200, err_msg
    global _TEST_APP
    _TEST_APP = None


@pytest.fixture(scope="session")
@log_method
def _test_app_callback_url(_create_test_app):
    return _create_test_app["callbackUrl"]


@pytest.fixture(scope="session")
@log_method
def _test_app_id(nhsd_apim_config):
    return nhsd_apim_config["APIGEE_APP_ID"]

@pytest.fixture()
@log_method
def trace(_apigee_proxy):
    """
    Authenticated wrapper around the DebugSessionsAPI class
    """
    config = ApigeeNonProdCredentials()
    client =  ApigeeClient(config=config)
    debug = DebugSessionsAPI(
        client=client,
        env_name=_apigee_proxy["environment"],
        api_name=_apigee_proxy["name"],
        revision_number=_apigee_proxy["revision"]
    )
    return debug

@pytest.fixture(scope="session")
@log_method
def access_token_api():
    """
    Authenitcated wrapper for Apigee's access token API
    """
    config = ApigeeNonProdCredentials()
    client = ApigeeClient(config=config)
    return AccessTokensAPI(client=client)


@pytest.fixture(scope="session")
@log_method
def products_api():
    """
    Authenitcated wrapper for Apigee's products API
    """
    config = ApigeeNonProdCredentials()
    client = ApigeeClient(config=config)
    return ApiProductsAPI(client=client)

@pytest.fixture(scope="session")
@log_method
def developer_apps_api():
    """
    Authenitcated wrapper for Apigee's developer apps API
    """
    config = ApigeeNonProdCredentials()
    client = ApigeeClient(config=config)
    return DeveloperAppsAPI(client=client)
