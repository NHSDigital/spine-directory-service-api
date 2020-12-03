from flask import request, abort

from app.http_headers import FHIR_CONTENT_TYPE, ANY_CONTENT_TYPE, JSON_CONTENT_TYPE


def check_accept_header():
    accept_types = request.headers['Accept'].lower()
    accept_types = accept_types.split(",")
    accept_types = list(map(lambda value: value.strip(), accept_types))

    if ANY_CONTENT_TYPE in accept_types or FHIR_CONTENT_TYPE in accept_types:
        return FHIR_CONTENT_TYPE
    elif JSON_CONTENT_TYPE in accept_types:
        return JSON_CONTENT_TYPE
    else:
        abort(406)
