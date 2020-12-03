import copy
import json
from urllib.parse import unquote

from flask import request

from app.matching_parameters import MatchingEndpointParameters, MatchingDeviceParameters
from app.utils import new_uuid


def load_stub(file):
    with open(file) as f:
        return json.load(f)


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
