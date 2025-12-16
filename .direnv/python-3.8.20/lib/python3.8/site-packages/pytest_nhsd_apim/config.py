"""
This module defines all the pytest config.

- command line flags
- ini options
- custom markers

And a few fixtures to pull that config in.
"""
import os
from datetime import datetime

import pytest

from .log import log_method

_PYTEST_CONFIG = {
    "--api-name": {
        "help": "Name of API. Should match the meta/api/name field in your manifest file.",
        "default": "",  # Must be falsy but not None.
    },
    "--proxy-name": {
        "help": "Proxy under test, should exactly match the name on Apigee.",
        "default": "",  # Must be falsy but not None.
    },
    "--apigee-access-token": {"help": "Access token to log into apigee edge API, output of get_token"},
    "--apigee-organization": {
        "help": "nhsd-nonprod/nhsd-prod.",
        "default": "nhsd-nonprod",
    },
    "--apigee-developer": {
        "help": "Developer that will own the test app.",
        "default": "apm-testing-internal-dev@nhs.net",
    },
    "--apigee-app-id": {
        "help": "Apigee ID of application under test. Required for tests in production environments.",
        "default": "", # Must be falsy but not None.
    },
    "--status-endpoint-api-key": {
        "help": "Used to authenticate calls to proxy's _status endpoint. Required for tests in production environments.",
        "default": "",  # Must be falsy but not None.
    },
    "--jwt-public-key-id": {
        "help": "Key ID ('kid') to select particular key.",
        "default": "test-1",
    },
    # TODO: Add these if the user wishes...
    # "--jwt-public-key-url": {
    #     "help": "URL of JWT public key. Must be used with --jwt-private-key-file.",
    #     "default": None
    # },
    # "--jwt-private-key-file": {
    #     "help": "Path to private key of JWT. Must be used with --jwt-public-key-url.",
    #     "default": None,
    # }
}


def _flag_to_dest(flag):
    # e.g. --apigee-access-token is stored as APIGEE_ACCESS_TOKEN
    return flag[2:].replace("-", "_").upper()


def pytest_addoption(parser):
    """
    Hook for cli options.

    Pytest calls this at some point to get command line flags into the
    request.config object.

    I also want to be able to define sensitive config, e.g.
    apigee_access_token via environment variables.
    """

    group = parser.getgroup("nhsd-apim")
    for flag, attrs in _PYTEST_CONFIG.items():
        group.addoption(
            flag,
            action="store",
            dest=_flag_to_dest(flag),
            help=attrs.get("help"),
            default=attrs.get("default"),
        )


def pytest_configure(config):
    """
    Hook for defining markers.
    """
    config.addinivalue_line(
        "markers",
        f"nhsd_apim_authorization(*args, **kwargs): Marker to define the authorization journey you want to take to get your access token or apikey.",
    )


@pytest.fixture(scope="session")
@log_method
def nhsd_apim_config(request):
    """
    Use this fixture to access this pytest extension's config.
    It checks environment variables as well as the CLI.
    """

    def _get_config(flag):
        name = _flag_to_dest(flag)

        cmd_line_value = getattr(request.config.option, name)
        if cmd_line_value is not None:
            return cmd_line_value

        env_var_value = os.environ.get(name)
        if env_var_value is not None:
            return env_var_value

        ve_msg = f"Missing required config. You must pass cli option {flag} or environment variable {name}."
        raise ValueError(ve_msg)

    return {_flag_to_dest(flag): _get_config(flag) for flag in _PYTEST_CONFIG}


@pytest.fixture()
@log_method
def nhsd_apim_api_name(nhsd_apim_config, request):
    marker = request.node.get_closest_marker("nhsd_apim_api_name")
    if marker:
        return marker.args[0]
    if nhsd_apim_config["API_NAME"]:
        return nhsd_apim_config["API_NAME"]
    raise ValueError("API_NAME is not defined.")


@pytest.fixture()
@log_method
def nhsd_apim_proxy_name(nhsd_apim_config, request):
    marker = request.node.get_closest_marker("nhsd_apim_proxy_name")
    if marker:
        return marker.args[0]
    if nhsd_apim_config["PROXY_NAME"]:
        return nhsd_apim_config["PROXY_NAME"]
    raise ValueError("PROXY_NAME is not defined.")
