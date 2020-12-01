import json
import os
import re
import uuid
from dataclasses import dataclass
from typing import Optional
import copy
from urllib.parse import unquote

from flask import Flask, request, abort, Response

app = Flask(__name__)

X_CORRELATION_ID = "X-Correlation-ID"
UUID_PATTERN = "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"

ORGANIZATION_QUERY_PARAMETER_NAME = "organization"
IDENTIFIER_QUERY_PARAMETER_NAME = "identifier"
MANAGING_ORGANIZATION_QUERY_PARAMETER_NAME = "managing-organization"

ORGANIZATION_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/ods-organization-code"
SERVICE_ID_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/nhsEndpointServiceId"
PARTY_KEY_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/nhsMhsPartyKey"
MANAGING_ORGANIZATION_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/ods-organization-code"

FHIR_CONTENT_TYPE = "application/fhir+json"

ENDPOINT_STUB_FILE = "stubs/endpoint.json"
DEVICE_STUB_FILE = "stubs/device.json"


def load_stub(file):
    with open(file) as f:
        return json.load(f)


@dataclass
class MatchingDeviceParameters:
    organization: str
    service_id: str
    party_key: str
    managing_organization: str

    def match(self, organization, service_id, party_key, managing_organization):
        return organization == self.organization and service_id == self.service_id \
               and (not party_key and not managing_organization
                    or managing_organization == self.managing_organization and not party_key
                    or not managing_organization and party_key == self.party_key
                    or managing_organization == self.managing_organization and party_key == self.party_key)


@dataclass
class MatchingEndpointParameters:
    organization: str
    service_id: str
    party_key: str

    def match(self, organization, service_id, party_key):
        return organization == self.organization \
               and (service_id == self.service_id and not party_key
                    or not service_id and party_key == self.party_key
                    or service_id == self.service_id and party_key == self.party_key)


_ENDPOINT_STUB = load_stub("stubs/endpoint.json")
ENDPOINT_QUERY_PARAMETERS = MatchingEndpointParameters(
    organization=_ENDPOINT_STUB["query_parameters"]["organization"],
    service_id=_ENDPOINT_STUB["query_parameters"]["service_id"],
    party_key=_ENDPOINT_STUB["query_parameters"]["party_key"])
ENDPOINT_RESPONSE_TEMPLATE = _ENDPOINT_STUB["response_body"]

_DEVICE_STUB = load_stub("stubs/device.json")
DEVICE_QUERY_PARAMETERS = MatchingDeviceParameters(
    organization=_DEVICE_STUB["query_parameters"]["organization"],
    service_id=_DEVICE_STUB["query_parameters"]["service_id"],
    party_key=_DEVICE_STUB["query_parameters"]["party_key"],
    managing_organization=_DEVICE_STUB["query_parameters"]["managing_organization"])
DEVICE_RESPONSE_TEMPLATE = _DEVICE_STUB["response_body"]


EMPTY_BUNDLE_TEMPLATE = load_stub("stubs/empty_bundle.json")
OPERATION_OUTCOME_400_TEMPLATE = load_stub("stubs/400.json")
OPERATION_OUTCOME_404_TEMPLATE = load_stub("stubs/404.json")
OPERATION_OUTCOME_405_TEMPLATE = load_stub("stubs/405.json")
OPERATION_OUTCOME_406_TEMPLATE = load_stub("stubs/406.json")


def new_uuid():
    return str(uuid.uuid4()).upper()


def build_empty_bundle():
    bundle = copy.deepcopy(EMPTY_BUNDLE_TEMPLATE)
    bundle["id"] = new_uuid()
    bundle["link"][0]["url"] = unquote(request.url)
    return bundle


def build_operation_outcome(operation_outcome_template, diagnostics):
    operation_outcome = copy.deepcopy(operation_outcome_template)
    operation_outcome["id"] = new_uuid()
    if diagnostics:
        operation_outcome["issue"][0]["diagnostics"] = diagnostics
    return operation_outcome


def build_bundle(bundle_stub_template):
    bundle = copy.deepcopy(bundle_stub_template)
    bundle["id"] = new_uuid()
    bundle["link"][0]["url"] = unquote(request.url)

    for entry in bundle["entry"]:
        resource_id = new_uuid()
        entry["resource"]["id"] = resource_id
        entry["fullUrl"] = f"{request.base_url}/{resource_id}"

    return bundle


def get_correlation_id(raise_error=True):
    correlation_id = request.headers.get(X_CORRELATION_ID, None)

    if not correlation_id:
        correlation_id = new_uuid()
    if len(re.findall(UUID_PATTERN, correlation_id)) != 1:
        if raise_error:
            abort(400, f"Invalid {X_CORRELATION_ID} header. Should be an UUIDv4 matching regex '{UUID_PATTERN}'")
        else:
            correlation_id = new_uuid()

    return correlation_id


def check_accept_header():
    accept_header = request.headers['Accept']
    if accept_header == "*/*":
        accept_header = FHIR_CONTENT_TYPE
    if accept_header != FHIR_CONTENT_TYPE:
        abort(406)


@app.route('/healthcheck')
def healthcheck():
    return {'status': 'OK'}


@app.route('/Endpoint', methods=['GET'])
def endpoint():
    correlation_id = get_correlation_id()

    organization = get_required_query_param(ORGANIZATION_QUERY_PARAMETER_NAME, ORGANIZATION_FHIR_IDENTIFIER)
    service_id = get_optional_query_param(IDENTIFIER_QUERY_PARAMETER_NAME, SERVICE_ID_FHIR_IDENTIFIER)
    party_key = get_optional_query_param(IDENTIFIER_QUERY_PARAMETER_NAME, PARTY_KEY_FHIR_IDENTIFIER)

    check_accept_header()

    if not service_id and not party_key:
        abort(400, f"HTTP 400: Missing or invalid '{IDENTIFIER_QUERY_PARAMETER_NAME}' query parameter. "
                   f"Should be one or both of: ["
                   f"'{IDENTIFIER_QUERY_PARAMETER_NAME}={SERVICE_ID_FHIR_IDENTIFIER}|value', "
                   f"'{IDENTIFIER_QUERY_PARAMETER_NAME}={PARTY_KEY_FHIR_IDENTIFIER}|value'")

    if ENDPOINT_QUERY_PARAMETERS.match(organization, service_id, party_key):
        bundle = build_bundle(ENDPOINT_RESPONSE_TEMPLATE)
    else:
        bundle = build_empty_bundle()

    return Response(
        json.dumps(bundle, indent=2, sort_keys=False),
        content_type=FHIR_CONTENT_TYPE,
        headers={"X-Correlation-ID": correlation_id})


@app.route('/Device', methods=['GET'])
def device():
    correlation_id = get_correlation_id()

    organization = get_required_query_param(ORGANIZATION_QUERY_PARAMETER_NAME, ORGANIZATION_FHIR_IDENTIFIER)
    service_id = get_required_query_param(IDENTIFIER_QUERY_PARAMETER_NAME, SERVICE_ID_FHIR_IDENTIFIER)
    party_key = get_optional_query_param(IDENTIFIER_QUERY_PARAMETER_NAME, PARTY_KEY_FHIR_IDENTIFIER)
    managing_organization = get_optional_query_param(MANAGING_ORGANIZATION_QUERY_PARAMETER_NAME, MANAGING_ORGANIZATION_FHIR_IDENTIFIER)

    check_accept_header()

    if DEVICE_QUERY_PARAMETERS.match(organization, service_id, party_key, managing_organization):
        bundle = build_bundle(DEVICE_RESPONSE_TEMPLATE)
    else:
        bundle = build_empty_bundle()

    return Response(
        json.dumps(bundle, indent=2, sort_keys=False),
        content_type=FHIR_CONTENT_TYPE,
        headers={"X-Correlation-ID": correlation_id})


def get_required_query_param(query_param_name: str, fhir_identifier: str) -> Optional[str]:
    value = get_optional_query_param(query_param_name, fhir_identifier)
    if not value:
        abort(400,
              f"HTTP 400: Missing or invalid '{query_param_name}' query parameter. Should be '{query_param_name}={fhir_identifier}|value'")
    return value


def get_optional_query_param(query_param_name: str, fhir_identifier: str) -> Optional[str]:
    values = list(filter(
        lambda value: "|" in value and value.split("|")[0] == fhir_identifier and value.split("|")[1],
        request.args.getlist(query_param_name)))

    last_value = values and values[-1]
    result_value = (last_value and last_value[last_value.index("|") + 1:]) or None
    return result_value


def operation_outcome_error_handler(template, status, diagnostics=None):
    correlation_id = get_correlation_id(raise_error=False)
    operation_outcome = build_operation_outcome(template, diagnostics)
    return Response(
        json.dumps(operation_outcome, indent=2, sort_keys=False),
        status=status,
        content_type=FHIR_CONTENT_TYPE,
        headers={"X-Correlation-ID": correlation_id})


@app.errorhandler(400)
def bad_request(error):
    return operation_outcome_error_handler(OPERATION_OUTCOME_400_TEMPLATE, error.code, error.description)


@app.errorhandler(404)
def page_not_found(error):
    return operation_outcome_error_handler(OPERATION_OUTCOME_404_TEMPLATE, error.code)


@app.errorhandler(405)
def method_not_allowed(error):
    return operation_outcome_error_handler(OPERATION_OUTCOME_405_TEMPLATE, error.code)


@app.errorhandler(406)
def not_acceptable(error):
    return operation_outcome_error_handler(OPERATION_OUTCOME_406_TEMPLATE, error.code)


if __name__ == '__main__':
    port = os.getenv("SDS_SANDBOX_SERVER_PORT") or 5000
    app.run(port=port)
