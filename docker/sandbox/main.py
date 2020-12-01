import json
import os
from typing import Optional

from flask import Flask, request, abort, Response
from app.http_headers import FHIR_CONTENT_TYPE
from app.accept_header_validator import check_accept_header
from app.correlation_id_reader import get_correlation_id
from app.stub_loader import build_empty_bundle, build_bundle, ENDPOINT_RESPONSE_TEMPLATE, ENDPOINT_QUERY_PARAMETERS, \
    DEVICE_QUERY_PARAMETERS, DEVICE_RESPONSE_TEMPLATE, build_operation_outcome, OPERATION_OUTCOME_400_TEMPLATE, \
    OPERATION_OUTCOME_404_TEMPLATE, OPERATION_OUTCOME_405_TEMPLATE, OPERATION_OUTCOME_406_TEMPLATE

app = Flask(__name__)

ORGANIZATION_QUERY_PARAMETER_NAME = "organization"
IDENTIFIER_QUERY_PARAMETER_NAME = "identifier"
MANAGING_ORGANIZATION_QUERY_PARAMETER_NAME = "managing-organization"

ORGANIZATION_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/ods-organization-code"
SERVICE_ID_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/nhsEndpointServiceId"
PARTY_KEY_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/nhsMhsPartyKey"
MANAGING_ORGANIZATION_FHIR_IDENTIFIER = "https://fhir.nhs.uk/Id/ods-organization-code"


@app.route('/healthcheck')
def healthcheck():
    return ""


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


def _operation_outcome_error_handler(template, status, diagnostics=None):
    correlation_id = get_correlation_id(raise_error=False)
    operation_outcome = build_operation_outcome(template, diagnostics)
    return Response(
        json.dumps(operation_outcome, indent=2, sort_keys=False),
        status=status,
        content_type=FHIR_CONTENT_TYPE,
        headers={"X-Correlation-ID": correlation_id})


@app.errorhandler(400)
def bad_request(error):
    return _operation_outcome_error_handler(OPERATION_OUTCOME_400_TEMPLATE, error.code, error.description)


@app.errorhandler(404)
def page_not_found(error):
    return _operation_outcome_error_handler(OPERATION_OUTCOME_404_TEMPLATE, error.code)


@app.errorhandler(405)
def method_not_allowed(error):
    return _operation_outcome_error_handler(OPERATION_OUTCOME_405_TEMPLATE, error.code)


@app.errorhandler(406)
def not_acceptable(error):
    return _operation_outcome_error_handler(OPERATION_OUTCOME_406_TEMPLATE, error.code)


if __name__ == '__main__':
    port = os.getenv("SDS_SANDBOX_SERVER_PORT") or 5000
    app.run(host="0.0.0.0", port=port)
