import re

from flask import request, abort

from app.utils import new_uuid

X_CORRELATION_ID = "X-Correlation-ID"
UUID_PATTERN = "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"


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
