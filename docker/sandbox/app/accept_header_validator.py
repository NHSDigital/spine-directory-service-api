from flask import request, abort

from app.http_headers import FHIR_CONTENT_TYPE, ANY_CONTENT_TYPE


def check_accept_header():
    accept_header = request.headers['Accept']
    if accept_header == ANY_CONTENT_TYPE:
        accept_header = FHIR_CONTENT_TYPE
    if accept_header != FHIR_CONTENT_TYPE:
        abort(406)
