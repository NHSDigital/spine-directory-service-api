from typing import Literal, Dict, Optional
import json
import base64
from functools import lru_cache

import pytest

from authlib.jose import jwk
from Crypto.PublicKey import RSA

from .log import log_method
from .token_cache import cache_tokens

from .identity_service import (
    ClientCredentialsConfig,
    ClientCredentialsAuthenticator,
    AuthorizationCodeConfig,
    AuthorizationCodeAuthenticator,
    TokenExchangeConfig,
    TokenExchangeAuthenticator,
    KeycloakUserConfig,
    KeycloakUserAuthenticator,
)


@log_method
@cache_tokens
def get_access_token_via_user_restricted_flow_separate_auth(
    identity_service_base_url,
    keycloak_client_credentials,
    login_form,
    apigee_client_id,
    jwt_private_key,
    jwt_kid,
    auth_scope: Literal["nhs-login", "nhs-cis2"],
    apigee_environment,
):
    if auth_scope == "nhs-cis2":
        # Get token from keycloak
        config = KeycloakUserConfig(
            realm=f"Cis2-mock-{apigee_environment}",
            client_id=keycloak_client_credentials["cis2"]["client_id"],
            client_secret=keycloak_client_credentials["cis2"]["client_secret"],
            login_form=login_form,
        )
        authenticator = KeycloakUserAuthenticator(config=config)
        id_token = authenticator.get_token()["id_token"]

    else:
        # Get token from keycloak
        config = KeycloakUserConfig(
            realm=f"NHS-Login-mock-{apigee_environment}",
            client_id=keycloak_client_credentials["nhs-login"]["client_id"],
            client_secret=keycloak_client_credentials["nhs-login"]["client_secret"],
            login_form=login_form,
        )
        authenticator = KeycloakUserAuthenticator(config=config)
        id_token = authenticator.get_token()["id_token"]

    # Exchange token
    config = TokenExchangeConfig(
        environment=apigee_environment,
        identity_service_base_url=identity_service_base_url,
        client_id=apigee_client_id,
        jwt_private_key=jwt_private_key,
        jwt_kid=jwt_kid,
        id_token=id_token,
    )
    authenticator = TokenExchangeAuthenticator(config=config)
    return authenticator.get_token()


@log_method
@cache_tokens
def get_access_token_via_user_restricted_flow_combined_auth(
    identity_service_base_url: str,
    client_id: str,
    client_secret: str,
    callback_url: str,
    auth_scope: Literal["nhs-login", "nhs-cis2"],
    login_form: Dict[str, str],
    apigee_environment,
):
    config = AuthorizationCodeConfig(
        environment=apigee_environment,
        callback_url=callback_url,
        identity_service_base_url=identity_service_base_url,
        client_id=client_id,
        client_secret=client_secret,
        scope=auth_scope,
        login_form=login_form,
    )
    authenticator = AuthorizationCodeAuthenticator(config=config)
    return authenticator.get_token()


@log_method
@cache_tokens
def get_access_token_via_signed_jwt_flow(
    identity_service_base_url: str,
    client_id: str,
    jwt_private_key: str,
    jwt_kid: str,
    apigee_environment,
):
    config = ClientCredentialsConfig(
        environment=apigee_environment,
        identity_service_base_url=identity_service_base_url,
        client_id=client_id,
        jwt_private_key=jwt_private_key,
        jwt_kid=jwt_kid,
    )
    authenticator = ClientCredentialsAuthenticator(config=config)
    return authenticator.get_token()


@lru_cache(maxsize=None)
@log_method
def create_jwt_key_pair(key_id):
    """
    Pure python instructions to generate a public-key/ private-key
    pair in the correct format.
    """
    key_size = 4096
    key = RSA.generate(key_size)
    private_key_pem = key.exportKey("PEM").decode()
    public_key_pem = key.publickey().exportKey("PEM").decode()

    # This is the JSON formatted public key
    json_web_key = jwk.dumps(
        public_key_pem, kty="RSA", crv_or_size=key_size, alg="RS512"
    )
    json_web_key["kid"] = key_id
    json_web_key["use"] = "sig"

    return {
        "public_key_pem": public_key_pem,
        "private_key_pem": private_key_pem,
        "json_web_key": {"keys": [json_web_key]},
    }


@pytest.fixture(scope="session")
@log_method
def jwt_public_key_id(nhsd_apim_config):
    return nhsd_apim_config["JWT_PUBLIC_KEY_ID"]


@pytest.fixture(scope="session")
@log_method
def _jwt_keys(jwt_public_key_id):
    return create_jwt_key_pair(jwt_public_key_id)


@pytest.fixture(scope="session")
@log_method
def jwt_private_key_pem(_jwt_keys):
    return _jwt_keys["private_key_pem"]


@pytest.fixture(scope="session")
@log_method
def jwt_public_key_pem(_jwt_keys):
    return _jwt_keys["public_key_pem"]


@pytest.fixture(scope="session")
@log_method
def jwt_public_key(_jwt_keys):
    """
    The JWT public key in JSON Web Key format.
    """
    return _jwt_keys["json_web_key"]


@pytest.fixture(scope="session")
@log_method
def jwt_public_key_url(jwt_public_key):
    jwt_public_key_string = json.dumps(jwt_public_key)
    encoded_public_key_bytes = base64.urlsafe_b64encode(jwt_public_key_string.encode())
    return f"https://internal-dev.api.service.nhs.uk/mock-jwks/{encoded_public_key_bytes.decode()}"
