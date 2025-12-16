from warnings import warn
from typing import Literal, Union, Dict, Any

import pytest
from typing_extensions import Annotated
from pydantic import BaseModel, Field

from .log import log_method


class BaseAuthorization(BaseModel):
    api_name: str
    force_new_token: bool = False

    def dict(self, **kwargs):
        """
        Construct the product scope when we export the Authorization
        subclasses.
        """
        # Yeah this breaks the inheritance encapsulation
        # slightly... but I'm tired.

        d = super().dict(**kwargs)
        access = d["access"]
        level = d["level"]
        ACCESS_SCOPE_PARTS = {
            "healthcare_worker": "user-nhs-cis2",
            "patient": "user-nhs-login",
            "application": "app",
        }
        scope = ":".join(
            ["urn:nhsd:apim", ACCESS_SCOPE_PARTS[access], level, self.api_name]
        )
        if access == "application" and level == "level0":
            scope = None
        d["scope"] = scope
        return d


class UserRestrictedAuthorization(BaseAuthorization):
    authentication: Literal["combined", "separate"] = "combined"
    login_form: Dict[str, Any] = Field(default_factory=dict)


class HealthcareWorkerAuthorization(UserRestrictedAuthorization):
    """
    Uses CIS2 as the identity provider
    """

    access: Literal["healthcare_worker"]
    level: Literal["aal1", "aal3"]



class PatientAuthorization(UserRestrictedAuthorization):
    """
    Uses NHSLogin as the identity provider
    """

    access: Literal["patient"]
    level: Literal["P0", "P5", "P9"]



class ApplicationAuthorization(BaseAuthorization):
    access: Literal["application"]
    level: Literal["level0", "level3"]


class Authorization(BaseModel):
    nhsd_apim_authorization: Annotated[
        Union[
            HealthcareWorkerAuthorization,
            PatientAuthorization,
            ApplicationAuthorization,
        ],
        Field(discriminator="access"),
    ]


@pytest.fixture()
@log_method
def nhsd_apim_authorization(request, nhsd_apim_api_name):
    """
    Mark your test with a `nhsd_apim_authorization marker`.
    Then call the `nhsd_apim_auth_headers` fixture to access your proxy.

    >>> import pytest
    >>> import requests
    >>> @pytest.mark.nhsd_apim_authorization(api_name="mock-jwks", access='healthcare_worker', level="aal3")
    >>> def test_application_restricted_access(nhsd_apim_proxy_url, nhsd_apim_auth_header):
    >>>     resp = requests.get(nhsd_apim_proxy_url + "/a/path/that/is/application/restricted",
    >>>                         headers=nhsd_apim_auth_header)
    >>>     assert resp.status_code == 200
    """
    marker = request.node.get_closest_marker("nhsd_apim_authorization")
    if marker is None:
        warn(
            "Could not find nhsd_apim_authorization marker. This will result in empty authorization headers. Explicitly set an empty @pytest.mark.nhsd_apim_authorization marker() to silence this warning."
        )
        return None

    if not marker.args and not marker.kwargs:
        return None

    if marker.args:
        auth_dict = marker.args[0]
    else:
        auth_dict = dict(**marker.kwargs)

    # Then use the fixture provided value... i.e. the direct marker
    # args override the fixture.
    if "api_name" not in auth_dict:
        auth_dict["api_name"] = nhsd_apim_api_name
    authorization = Authorization(nhsd_apim_authorization=auth_dict)
    return authorization.dict()["nhsd_apim_authorization"]
